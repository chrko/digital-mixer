from digimix.audio.base import AudioMode
from digimix.audio.inputs import SingleJackClientInput


def test_input_patch_panel():
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
    desc = ' '.join(desc.replace('\n', ' ').split()).replace('(', '\\(').replace(')', '\\)')
    print(desc)
