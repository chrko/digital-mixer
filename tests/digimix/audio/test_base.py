from digimix.audio.base import Stereo2Mono
from digimix.audio.gstreamer.utils import escape_pipeline_description


def test_stereo_to_mono():
    bin_desc = """
        jackaudiosrc connect=0 client-name=StereoTest
        ! stereo2mono_sink-test.
    """
    bin_desc += Stereo2Mono('test', level_db=-6).pipeline_description
    bin_desc += """
        stereo2mono_src-test.
        ! jackaudiosink connect=0 client-name=MonoSum
    """

    print(bin_desc)
    print(escape_pipeline_description(bin_desc))
