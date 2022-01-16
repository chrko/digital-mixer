from digimix.audio.base import AudioMode
from digimix.audio.io.jack import MultiJackClientInput, SingleJackClientInput, SingleJackClientOutput
from digimix.audio.utils import escape_pipeline_description


class TestSingleJackClientInput:
    def test_pipeline_description(self):
        in_patch_panel = SingleJackClientInput(
            "test",
            (
                ("music", AudioMode.STEREO),
                ("mic", AudioMode.MONO),
            ),
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
            "test",
            (
                ("music", AudioMode.STEREO),
                ("mic", AudioMode.MONO),
            ),
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


class TestSingleJackClientOutput:
    def test_pipeline_description(self):
        in_patch_panel = SingleJackClientInput(
            "test",
            (
                ("music", AudioMode.STEREO),
                ("mic", AudioMode.MONO),
            ),
        )
        desc = in_patch_panel.pipeline_description
        out_patch_panel = SingleJackClientOutput(
            "test",
            (
                ("music", AudioMode.STEREO),
                ("mic", AudioMode.MONO),
            ),
        )
        desc += out_patch_panel.pipeline_description
        desc += f"""
        {in_patch_panel.src[0]}.
        ! {out_patch_panel.sink[0]}.
        {in_patch_panel.src[1]}.
        ! {out_patch_panel.sink[1]}.
        """

        print(desc)
        print(escape_pipeline_description(desc))
