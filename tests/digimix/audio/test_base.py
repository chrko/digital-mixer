from digimix.audio.base import AudioMode, InputPatchPanel


def test_input_patch_panel():
    bin = InputPatchPanel(
        'test',
        (
            ('music', AudioMode.STEREO),
            ('mic', AudioMode.MONO),
        )
    )
    desc = bin.pipeline_description
    desc += f"""
    audiomixer name=mix

    jack_src-music.
    ! audiopanorama
    ! mix.
    jack_src-mic.
    ! audiopanorama
    ! mix.

    mix. ! jackaudiosink connect=0 name=jacksink client-name=GstSink
    """

    print(desc)
    desc = ' '.join(desc.replace('\n', ' ').split()).replace('(', '\\(').replace(')', '\\)')
    print(desc)
