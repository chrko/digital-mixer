import mido

midi_backend = mido.Backend('mido.backends.rtmidi/UNIX_JACK')

in_port = midi_backend.open_input(client_name='DigitalMixerControl In', name='midi_in', virtual=True)
out_port = midi_backend.open_output(client_name='DigitalMixerControl Out', name='midi_out', virtual=True)
