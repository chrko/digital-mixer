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
            ("mic", AudioMode.MONO),
            ("ms_teams", AudioMode.STEREO),
            ("music", AudioMode.STEREO),
            ("other", AudioMode.MONO),
        )
    )

    mic = FaderChannel(
        name="mic",
    )
    ms_teams = FaderChannel(name="ms_teams")
    music = FaderChannel(name="music")
    other = FaderChannel(name="other")

    master = MasterBus(name="master", inputs=[
        mic.src[0],
        ms_teams.src[0],
        music.src[0],
        other.src[0],
    ])

    out = SingleJackClientOutput(
        name="main_out",
        conf=(
            ("main", AudioMode.STEREO),
        )
    )

    desc = ""
    desc += src.pipeline_description + "\n"
    desc += mic.pipeline_description + "\n"
    desc += ms_teams.pipeline_description + "\n"
    desc += music.pipeline_description + "\n"
    desc += other.pipeline_description + "\n"
    desc += master.pipeline_description + "\n"
    desc += out.pipeline_description + "\n"

    desc += f"{src.src[0]}. ! {mic.sink[0]}." + "\n"
    desc += f"{src.src[2]}. ! {ms_teams.sink[0]}." + "\n"
    desc += f"{src.src[1]}. ! {music.sink[0]}." + "\n"
    desc += f"{src.src[3]}. ! {other.sink[0]}." + "\n"
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
