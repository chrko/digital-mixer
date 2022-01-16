import threading
import time

from digimix.audio import GLib, Gst
from digimix.audio.base import AudioMode
from digimix.audio.buses import MasterBus
from digimix.audio.channels import FaderChannel
from digimix.audio.io.jack import SingleJackClientOutput
from digimix.audio.io.pipewire import PipewireInput
from digimix.audio.utils import default_linear_fader_midi_to_db
from digimix.midi.devices.akai_midimix import MidiMix
from digimix.midi.jack_io import RtMidiJackIO
from digimix.utils.debug.gstreamer import gst_generate_dot

if __name__ == "__main__":
    midi_io = RtMidiJackIO("DigitalMixerControl")
    hw = MidiMix(midi_io)

    src = PipewireInput(
        name="main_in",
        conf=(
            ("mic", AudioMode.MONO),
            ("ms_teams", AudioMode.STEREO),
            ("music", AudioMode.STEREO),
            ("other", AudioMode.MONO),
        ),
    )

    mic = FaderChannel(
        name="mic",
    )
    ms_teams = FaderChannel(name="ms_teams")
    music = FaderChannel(name="music")
    other = FaderChannel(name="other")

    master = MasterBus(
        name="master",
        inputs=[
            mic.src[0],
            ms_teams.src[0],
            music.src[0],
            other.src[0],
        ],
    )

    out = SingleJackClientOutput(name="main_out", conf=(("main", AudioMode.STEREO),))

    els = [
        src,
        mic,
        ms_teams,
        music,
        other,
        master,
        out,
    ]

    p_descs = [el.pipeline_description for el in els] + [
        f"{src.src[0]}. ! {mic.sink[0]}.",
        f"{src.src[1]}. ! {ms_teams.sink[0]}.",
        f"{src.src[2]}. ! {music.sink[0]}.",
        f"{src.src[3]}. ! {other.sink[0]}.",
        f"{master.src[0]}. ! {out.sink[0]}.",
    ]

    desc = "\n".join(p_descs)

    print(desc)

    main = GLib.MainLoop()
    pipeline = Gst.parse_launch(desc)  # type: Gst.Pipeline
    assert pipeline
    pipeline.set_state(Gst.State.PLAYING)
    for el in els:
        el.attach_pipeline(pipeline)

    def fader_channel_fader_callback_maker(fader: FaderChannel):
        def callback(new_value, *_, **__):
            fader.fader_db = default_linear_fader_midi_to_db(new_value)

        return callback

    hw.faders[0].add_callback(fader_channel_fader_callback_maker(mic))
    hw.faders[1].add_callback(fader_channel_fader_callback_maker(ms_teams))
    hw.faders[2].add_callback(fader_channel_fader_callback_maker(music))
    hw.faders[3].add_callback(fader_channel_fader_callback_maker(other))

    def dotter():
        while True:
            gst_generate_dot(pipeline, str(int(time.time())))
            time.sleep(5)

    dotter_thread = threading.Thread(name="Dotter", target=dotter, daemon=True)
    # dotter_thread.start()

    try:
        hw.start_feeder()
        main.run()
    except KeyboardInterrupt:
        midi_io.delete()
        main.quit()
