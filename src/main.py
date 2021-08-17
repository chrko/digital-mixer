from threading import Thread

from digimix.midi.devices.akai_midimix import MidiMix
from digimix.midi.jack_io import RtMidiJackIO

if __name__ == '__main__':
    io = RtMidiJackIO('DigitalMixerControl')
    mix = MidiMix(io)


    def feed_events():
        while msg := io.receive():
            mix.dispatcher.dispatch(msg)


    feeder = Thread(name='Feeder', target=feed_events)
    feeder.start()
