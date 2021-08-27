import threading
import time

from digimix.audio import GLib, Gst
from digimix.audio.channels import FaderChannel
from digimix.utils.debug.gstreamer import gst_generate_dot

if __name__ == '__main__':
    el = FaderChannel(name="mic")

    desc = f"jackaudiosrc connect=0 client-name=FaderChannelIn ! {el.sink[0]}. "
    desc += el.pipeline_description
    desc += f"{el.src[0]}. ! jackaudiosink connect=0 client-name=FaderChannelOut"

    main = GLib.MainLoop()
    pipeline = Gst.parse_launch(desc)  # type: Gst.Pipeline
    assert pipeline
    pipeline.set_state(Gst.State.PLAYING)
    el.attach_pipeline(pipeline)


    def threader():
        time.sleep(2)
        gst_generate_dot(pipeline, "1")
        el.cut = True
        gst_generate_dot(pipeline, "2")
        time.sleep(0.5)
        el.cut = False
        el.pan = -0.5
        gst_generate_dot(pipeline, "3")
        time.sleep(0.5)
        el.fader_db = -10
        gst_generate_dot(pipeline, "4")
        time.sleep(2)
        main.quit()


    t = threading.Thread(name="fader_channel_tester", target=threader)
    t.start()

    try:
        main.run()
    except KeyError:
        main.quit()
