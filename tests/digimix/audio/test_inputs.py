from digimix.audio.base import AudioMode
from digimix.audio.gstreamer.utils import escape_pipeline_description
from digimix.audio.inputs import MultiJackClientInput, SingleJackClientInput


def test_SingleJackClientInput():
    in_patch_panel = SingleJackClientInput(
        'test',
        (
            ('music', AudioMode.STEREO),
            ('mic', AudioMode.MONO),
        )
    )
    desc = in_patch_panel.pipeline_description
    desc += f"""
    audiomixer name=mix

    src-music.
    ! audiopanorama
    ! mix.
    src-mic.
    ! audiopanorama
    ! mix.

    mix. ! jackaudiosink connect=0 name=jacksink client-name=GstSink
    """

    print(desc)
    print(escape_pipeline_description(desc))


def test_MultiJackClientInput():
    in_patch_panel = MultiJackClientInput(
        'test',
        (
            ('music', AudioMode.STEREO),
            ('mic', AudioMode.MONO),
        )
    )
    desc = in_patch_panel.pipeline_description
    desc += f"""
    audiomixer name=mix

    src-music.
    ! audiopanorama
    ! mix.
    src-mic.
    ! audiopanorama
    ! mix.

    mix. ! jackaudiosink connect=0 name=jacksink client-name=GstSink
    """

    print(desc)
    print(escape_pipeline_description(desc))
