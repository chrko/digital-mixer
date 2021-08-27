from digimix.audio.base import AudioMode
from digimix.audio.inputs import MultiJackClientInput, SingleJackClientInput
from digimix.audio.utils import escape_pipeline_description


class TestSingleJackClientInput:
    def test_pipeline_description(self):
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

        {in_patch_panel.src[0]}.
        ! audiopanorama
        ! mix.
        {in_patch_panel.src[1]}.
        ! audiopanorama
        ! mix.

        mix. ! jackaudiosink connect=0 name=jacksink client-name=GstSink
        """

        print(desc)
        print(escape_pipeline_description(desc))


class TestMultiJackClientInput:
    def test_pipeline_description(self):
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

        {in_patch_panel.src[0]}.
        ! audiopanorama
        ! mix.
        {in_patch_panel.src[1]}.
        ! audiopanorama
        ! mix.

        mix. ! jackaudiosink connect=0 name=jacksink client-name=GstSink
        """

        print(desc)
        print(escape_pipeline_description(desc))
