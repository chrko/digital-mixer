from mido.messages import Message

from digimix.midi.dispatcher import MidiDispatcher


def test_midi_msg_matching():
    def note_on_callable(*_, **__):
        note_on_callable.calls += 1
        assert note_on_callable.calls == 1

    note_on_callable.calls = 0
    note_on_part_msg = {
        "type": "note_on",
        "channel": 0,
        "note": 0,
    }

    msg = Message(type="note_on", channel=0)

    dispatcher = MidiDispatcher()

    dispatcher.add_callback(note_on_part_msg, note_on_callable)
    dispatcher.dispatch(msg)

    msg = Message(type="note_on", channel=0, note=1)
    dispatcher.dispatch(msg)

    msg = Message(type="note_off")
    dispatcher.dispatch(msg)
