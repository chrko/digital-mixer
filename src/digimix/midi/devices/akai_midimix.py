from mido.messages import Message

from digimix.midi.dispatcher import MidiDispatcher
from digimix.midi.generic_controls import Button, ContinuousControlReadOnly
from digimix.midi.jack_io import RtMidiJackIO


def make_led_handler(midi_io: RtMidiJackIO, note: int, channel: int = 0):
    led_on_msg = Message(
        type='note_on',
        channel=channel,
        note=note,
        velocity=127,
    )
    led_off_msg = Message(
        type='note_on',
        channel=channel,
        note=note,
        velocity=0,
    )

    def led_handler(caller: Button, *_, **__):
        if caller.active:
            midi_io.send(led_on_msg)
        else:
            midi_io.send(led_off_msg)

    return led_handler


class MidiMix:
    def __init__(self, midi_io: RtMidiJackIO):
        self.midi_io = midi_io
        self._dispatcher = MidiDispatcher()

        ccs = [
            ContinuousControlReadOnly(
                name=f'CC_{row}_{col}',
                min_value=0,
                max_value=127,
            )
            for col in range(8)
            for row in range(4)
        ]
        master_fader = ContinuousControlReadOnly(
            name='Master',
            min_value=0,
            max_value=127
        )

        self._faders = tuple([cc for i, cc in enumerate(ccs) if i % 4 == 3] + [master_fader])
        self._knob_matrix = tuple(tuple(ccs[row + col * 4] for col in range(8)) for row in range(3))

        buttons = [
                      Button(
                          name=f'Button_{row}_{col}',
                          mode=Button.Mode.TIMED_TOGGLE,
                      )
                      for row in range(3)
                      for col in range(8)
                  ] + [
                      Button(
                          name='Bank_left',
                          mode=Button.Mode.MOMENTARY,
                      ),
                      Button(
                          name='Bank_right',
                          mode=Button.Mode.MOMENTARY,
                      ),
                      Button(
                          name='Solo_shift',
                          mode=Button.Mode.MOMENTARY,
                      )
                  ]
        self._button_matrix = tuple(tuple(buttons[row + col * 3] for col in range(8)) for row in range(3))
        self._special_buttons = tuple(buttons[-3:])

        channels = []

        for col in range(8):
            channel = (
                ccs[col * 4],
                ccs[col * 4 + 1],
                ccs[col * 4 + 2],
                buttons[col * 3],
                buttons[col * 3 + 1],
                buttons[col * 3 + 2],
                ccs[col * 4 + 3],
            )
            channel[0].name = f'Knob_ch{col}_1'
            channel[1].name = f'Knob_ch{col}_2'
            channel[2].name = f'Knob_ch{col}_3'
            channel[3].name = f'Button_ch{col}_Mute'
            channel[4].name = f'Button_ch{col}_Solo'
            channel[5].name = f'Button_ch{col}_Rec'
            channel[6].name = f'Fader_ch{col}'
            channels.append(channel)
        self._channels = tuple(channels)

        for i, cc in enumerate(ccs + [master_fader]):
            self._dispatcher.add_callback(
                partial_msg_dict={
                    'type': 'control_change',
                    'channel': 0,
                    'control': 15 + i
                },
                callback=cc.midi_message_extractor
            )

        for i, button in enumerate(buttons):
            self._dispatcher.add_callback(
                partial_msg_dict={
                    'type': 'note_on',
                    'channel': 0,
                    'note': i,
                    'velocity': 127,
                },
                callback=button.press,
            )
            self._dispatcher.add_callback(
                partial_msg_dict={
                    'type': 'note_off',
                    'channel': 0,
                    'note': i,
                    'velocity': 127,
                },
                callback=button.release,
            )
            button.add_callback(make_led_handler(midi_io=midi_io, note=i))

    @property
    def channels(self) -> tuple[tuple[
        ContinuousControlReadOnly, ContinuousControlReadOnly, ContinuousControlReadOnly, Button, Button, Button, ContinuousControlReadOnly
    ]]:
        return self._channels

    @property
    def knob_matrix(self) -> tuple[tuple[ContinuousControlReadOnly]]:
        return self._knob_matrix

    @property
    def button_matrix(self) -> tuple[tuple[Button]]:
        return self._button_matrix

    @property
    def faders(self) -> tuple[ContinuousControlReadOnly]:
        return self._faders

    @property
    def special_buttons(self) -> tuple[Button]:
        return self._special_buttons

    @property
    def dispatcher(self) -> MidiDispatcher:
        return self._dispatcher
