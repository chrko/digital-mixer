import typing

from mido.messages import checks, Message

from digimix.utils.dicts import dict_to_tuple


class MidiDispatcher:
    def __init__(self):
        self._midi_callback_map = {}

    def add_callback(self, partial_msg_dict: typing.Dict, callback: typing.Callable):
        checks.check_msgdict(partial_msg_dict)

        key = dict_to_tuple(partial_msg_dict)
        if key not in self._midi_callback_map:
            self._midi_callback_map[key] = set()  # weakref.WeakSet()
        self._midi_callback_map[key].add(callback)

    def dispatch(self, msg: Message):
        if not isinstance(msg, Message):
            return
        msg_dict_view = msg.dict().items()
        for partial_msg_dict, callbacks in self._midi_callback_map.items():
            if dict(partial_msg_dict).items() <= msg_dict_view:
                for callback in callbacks:
                    if callback:
                        callback(msg=msg)
