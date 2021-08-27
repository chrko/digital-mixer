from digimix.audio.base import Stereo2Mono
from digimix.audio.gstreamer.utils import escape_pipeline_description


def test_stereo_to_mono():
    el = Stereo2Mono('test', level_db=-6)

    bin_desc = f"""
        jackaudiosrc connect=0 client-name=StereoTest
        ! {el.sink[0]}.
    """
    bin_desc += el.pipeline_description
    bin_desc += f"""
        {el.src[0]}.
        ! jackaudiosink connect=0 client-name=MonoSum
    """

    print(bin_desc)
    print(escape_pipeline_description(bin_desc))
