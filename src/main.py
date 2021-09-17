import threading
import time

from digimix.audio import GLib, Gst
from digimix.audio.base import AudioMode
from digimix.audio.buses import MasterBus
from digimix.audio.channels import FaderChannel
from digimix.audio.io.jack import SingleJackClientInput, SingleJackClientOutput
from digimix.utils.debug.gstreamer import gst_generate_dot

if __name__ == '__main__':
    src = SingleJackClientInput(
        name="main_in",
        conf=(
            ("mic1", AudioMode.MONO),
            ("music", AudioMode.STEREO),
            ("drums", AudioMode.STEREO),
            ("bass", AudioMode.MONO),
            ("guitar", AudioMode.MONO),
        )
    )

    mic1 = FaderChannel(
        name="mic1",
    )
    music = FaderChannel(name="music")
    drums = FaderChannel(name="drums")
    bass = FaderChannel(name="bass")
    guitar = FaderChannel(name="guitar")

    master = MasterBus(name="master", inputs=[
        mic1.src[0],
        music.src[0],
        drums.src[0],
        bass.src[0],
        guitar.src[0],
    ])

    out = SingleJackClientOutput(
        name="main_out",
        conf=(
            ("main", AudioMode.STEREO),
        )
    )

    desc = ""
    desc += src.pipeline_description + "\n"
    desc += mic1.pipeline_description + "\n"
    desc += music.pipeline_description + "\n"
    desc += drums.pipeline_description + "\n"
    desc += bass.pipeline_description + "\n"
    desc += guitar.pipeline_description + "\n"
    desc += master.pipeline_description + "\n"
    desc += out.pipeline_description + "\n"

    desc += f"{src.src[0]}. ! {mic1.sink[0]}." + "\n"
    desc += f"{src.src[1]}. ! {music.sink[0]}." + "\n"
    desc += f"{src.src[2]}. ! {drums.sink[0]}." + "\n"
    desc += f"{src.src[3]}. ! {bass.sink[0]}." + "\n"
    desc += f"{src.src[4]}. ! {guitar.sink[0]}." + "\n"
    desc += f"{master.src[0]}. ! {out.sink[0]}." + "\n"

    print(desc)

    main = GLib.MainLoop()
    pipeline = Gst.parse_launch(desc)  # type: Gst.Pipeline
    assert pipeline
    pipeline.set_state(Gst.State.PLAYING)
    music.attach_pipeline(pipeline)


    def threader():
        time.sleep(2)
        gst_generate_dot(pipeline, "1")
        music.cut = True
        gst_generate_dot(pipeline, "2")
        time.sleep(0.5)
        music.cut = False
        music.pan = -0.5
        gst_generate_dot(pipeline, "3")
        time.sleep(0.5)
        music.fader_db = -10
        gst_generate_dot(pipeline, "4")
        time.sleep(2)
        main.quit()


    t = threading.Thread(name="fader_channel_tester", target=threader)
    t.start()

    try:
        main.run()
    except KeyError:
        main.quit()
