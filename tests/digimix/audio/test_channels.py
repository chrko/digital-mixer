from digimix.audio.channels import FaderChannel
from digimix.audio.gstreamer.utils import escape_pipeline_description


class TestFaderChannel:
    def test_pipeline_description(self):
        el = FaderChannel(name="mic")

        desc = f"""
        jackaudiosrc connect=0 client-name=FaderChannelIn
        ! {el.sink[0]}.
        """
        desc += el.pipeline_description
        desc += f"""
        {el.src[0]}.
        ! jackaudiosink connect=0 client-name=FaderChannelOut
        """

        print(desc)
        print(escape_pipeline_description(desc))
