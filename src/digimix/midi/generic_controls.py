import enum
import threading
import typing
from fractions import Fraction

from mido.messages import Message
from transitions import State
from transitions.extensions import MachineFactory

from digimix.utils.callbacks import CallbackBase
from digimix.utils.enum import AutoNumber

Machine = MachineFactory.get_predefined(
    locked=True,
)


class ContinuousControlReadOnly(CallbackBase):
    PICK_UP_RANGE = Fraction(4, 100)

    @enum.unique
    class Behaviour(AutoNumber):
        JUMP = ()
        PICK_UP = ()

    def __init__(
        self,
        name: str = '',
        initial_value: int = 0,
        min_value: int = 0,
        max_value: int = 127,
        map_min_value=0,
        map_max_value=1,
        behaviour: Behaviour = Behaviour.JUMP,
    ):
        super().__init__()
        self._name = str(name)

        self._value = int(initial_value)
        self._value_lock = threading.RLock()

        self._min_value = int(min_value)
        self._max_value = int(max_value)

        self._map_min_value = map_min_value
        self._map_max_value = map_max_value
        self._map_value_range_lock = threading.RLock()

        self._behaviour = behaviour

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_value: str):
        self._name = str(new_value)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, new_value: int):
        with self._value_lock:
            if self._behaviour is self.Behaviour.PICK_UP:
                if not (abs(self._value - new_value) <= self.PICK_UP_RANGE * self._max_value):
                    return
                self._behaviour = self.Behaviour.JUMP
            new_value = int(new_value)
            old_value = self.value
            self._value = new_value
            if old_value != new_value:
                with self._callback_lock:
                    for callback in self._callbacks:
                        callback(caller=self, old_value=old_value, new_value=new_value)

    @property
    def min_value(self) -> int:
        return self._min_value

    @property
    def max_value(self) -> int:
        return self._max_value

    @property
    def mapped_value(self):
        with self._map_value_range_lock:
            return self._map_min_value + (
                Fraction(self._value - self._min_value, self._max_value - self._min_value)
                *
                (self._map_max_value - self._map_min_value)
            )

    @property
    def behaviour(self) -> Behaviour:
        return self._behaviour

    @behaviour.setter
    def behaviour(self, new_value: Behaviour):
        with self._value_lock:
            self._behaviour = new_value

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} ' \
               f'name={self.name} ' \
               f'value={self.value} ' \
               f'mapped_value={self.mapped_value} ' \
               f'behaviour={self.behaviour}>'

    def midi_message_extractor(self, msg: Message):
        if msg.type == 'control_change':
            self.value = msg.value


class ButtonState(State):
    def __init__(self, name: str, pressed: bool, active: bool, on_enter=None, on_exit=None,
                 ignore_invalid_triggers=None):
        super().__init__(
            name=name,
            on_enter=on_enter,
            on_exit=on_exit,
            ignore_invalid_triggers=ignore_invalid_triggers
        )
        self._pressed = pressed
        self._active = active

    @property
    def pressed(self) -> bool:
        return self._pressed

    @property
    def active(self) -> bool:
        return self._active

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and self._active is other._active
            and self._pressed is other._pressed
        )


class Button(CallbackBase):
    TIMED_TOGGLE_DELAY_MS = 500

    @enum.unique
    class Mode(enum.Flag):
        TOGGLE = enum.auto()
        MOMENTARY = enum.auto()
        TIMED_TOGGLE = TOGGLE | MOMENTARY

    MACHINE_DICT = {
        Mode.MOMENTARY: Machine(
            name='ButtonMomentaryMachine',
            model=None,
            states=[
                ButtonState(name='released', pressed=False, active=False),
                ButtonState(name='pressed', pressed=True, active=True),
            ],
            initial='released',
            transitions=[
                {'source': 'released', 'trigger': 'press', 'dest': 'pressed'},
                {'source': 'pressed', 'trigger': 'release', 'dest': 'released'},
            ],
            send_event=True,
            auto_transitions=False,
            ordered_transitions=False,
            ignore_invalid_triggers=True,
            before_state_change=None,
            after_state_change='_trigger_callbacks',
            queued=False,
        ),
        Mode.TOGGLE: Machine(
            name='ButtonToggleMachine',
            model=None,
            states=[
                ButtonState(name='released_inactive', pressed=False, active=False),
                ButtonState(name='released_active', pressed=False, active=True),
                ButtonState(name='pressed_active', pressed=True, active=True),
                ButtonState(name='pressed_inactive', pressed=True, active=False),
            ],
            initial='released_inactive',
            transitions=[
                {'source': 'released_inactive', 'trigger': 'press', 'dest': 'pressed_active'},
                {'source': 'pressed_active', 'trigger': 'release', 'dest': 'released_active'},
                {'source': 'released_active', 'trigger': 'press', 'dest': 'pressed_inactive'},
                {'source': 'pressed_inactive', 'trigger': 'release', 'dest': 'released_inactive'},
            ],
            send_event=True,
            auto_transitions=False,
            ordered_transitions=False,
            ignore_invalid_triggers=True,
            before_state_change=None,
            after_state_change='_trigger_callbacks',
            queued=False,
        ),
        Mode.TIMED_TOGGLE: Machine(
            name='ButtonTimedToggleMachine',
            model=None,
            states=[
                ButtonState(name='released_inactive', pressed=False, active=False),
                ButtonState(
                    name='toggle_pressed_active',
                    pressed=True,
                    active=True,
                    on_enter='_start_momentary_timeout',
                    on_exit='_stop_momentary_timeout'
                ),
                ButtonState(name='toggle_released_active', pressed=False, active=True),
                ButtonState(name='toggle_pressed_inactive', pressed=True, active=False),
                ButtonState(name='momentary_pressed_active', pressed=True, active=True),
            ],
            initial='released_inactive',
            transitions=[
                {'source': 'released_inactive', 'trigger': 'press', 'dest': 'toggle_pressed_active'},
                {'source': 'toggle_pressed_active', 'trigger': 'release', 'dest': 'toggle_released_active'},
                {'source': 'toggle_released_active', 'trigger': 'press', 'dest': 'toggle_pressed_inactive'},
                {'source': 'toggle_pressed_inactive', 'trigger': 'release', 'dest': 'released_inactive'},
                {'source': 'toggle_pressed_active', 'trigger': 'momentary_timeout', 'dest': 'momentary_pressed_active'},
                {'source': 'momentary_pressed_active', 'trigger': 'release', 'dest': 'released_inactive'},
            ],
            send_event=True,
            auto_transitions=False,
            ordered_transitions=False,
            ignore_invalid_triggers=True,
            before_state_change=None,
            after_state_change='_trigger_callbacks',
            queued=False,
        ),
    }

    state: str
    press: typing.Callable
    release: typing.Callable
    momentary_timeout: typing.Callable

    def __init__(
        self,
        name: str = '',
        mode: Mode = Mode.TOGGLE,
    ):
        super().__init__()
        self._name = str(name)

        self._mode = mode

        self._machine = self.MACHINE_DICT[self._mode]
        self._machine.add_model(self)

        self._momentary_timeout_timer: typing.Optional[threading.Timer] = None

    def __del__(self):
        self._machine.remove_model(self)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_value: str):
        self._name = str(new_value)

    def _start_momentary_timeout(self, *_, **__):
        if self._momentary_timeout_timer is not None:
            self._momentary_timeout_timer.cancel()
        self._momentary_timeout_timer = threading.Timer(
            self.TIMED_TOGGLE_DELAY_MS / 1000,
            self.momentary_timeout,
        )
        self._momentary_timeout_timer.daemon = True
        self._momentary_timeout_timer.start()

    def _stop_momentary_timeout(self, *_, **__):
        if self._momentary_timeout_timer is not None:
            self._momentary_timeout_timer.cancel()
            self._momentary_timeout_timer = None

    def _trigger_callbacks(self, event, **__):
        with self._callback_lock:
            for callback in self._callbacks:
                callback(caller=self, event=event)

    @property
    def pressed(self) -> bool:
        return self._machine.get_state(self.state).pressed

    @property
    def active(self) -> bool:
        return self._machine.get_state(self.state).active

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} ' \
               f'name={self.name} ' \
               f'pressed={self.pressed} ' \
               f'active={self.active} ' \
               f'mode={self._mode}>'
