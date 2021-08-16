import threading
from queue import SimpleQueue

import mido.messages.messages
import rtmidi
from mido.messages import Message


class RtMidiJackIO:
    API = rtmidi.API_UNIX_JACK

    def __init__(self, client_name_prefix: str):
        self._msg_queue_in = SimpleQueue()

        self._in_client = rtmidi.MidiIn(
            rtapi=self.API,
            name=client_name_prefix + 'In'
        )
        self._in_client.ignore_types(False, True, True)
        self._in_client.open_virtual_port(name='Midi In')
        self._in_client.set_callback(self._rtmidi_input_callback)

        self._send_lock = threading.RLock()
        self._out_client = rtmidi.MidiOut(
            rtapi=self.API,
            name=client_name_prefix + 'Out'
        )
        self._out_client.open_virtual_port(name='Midi Out')

    def _rtmidi_input_callback(self, msg_data, _):
        try:
            self._msg_queue_in.put(Message.from_bytes(msg_data[0]))
        except ValueError:
            pass

    def receive(self) -> mido.messages.Message:
        return self._msg_queue_in.get()

    def send(self, msg: mido.messages.Message):
        with self._send_lock:
            self._out_client.send_message(msg.bytes())

    def delete(self):
        self._in_client.delete()
        self._out_client.delete()
