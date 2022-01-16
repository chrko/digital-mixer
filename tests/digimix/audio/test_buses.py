from digimix.audio.base import AudioMode
from digimix.audio.buses import MasterBus
from digimix.audio.channels import FaderChannel
from digimix.audio.io.jack import JackClientInput, SingleJackClientInput
from digimix.audio.utils import escape_pipeline_description


class TestMasterBus:
    def test_pipeline_description(self):
        ins = SingleJackClientInput(
            name="JackIn",
            conf=(
                ("mic", AudioMode.MONO),
                ("teams", AudioMode.STEREO),
                ("music", AudioMode.STEREO),
            ),
        )
        desc = ins.pipeline_description

        faders = []
        for in_name, in_src in zip(["mic", "teams", "music"], ins.src):
            fader = FaderChannel(name=in_name)
            desc += fader.pipeline_description
            desc += f"""
                {in_src}.
                ! {fader.sink[0]}.
            """
            faders.append(fader)

        el = MasterBus(name="main", inputs=[fader.src[0] for fader in faders])

        desc += el.pipeline_description
        desc += f"""
            {el.src[0]}.
            ! queue
            ! jackaudiosink
                connect=0
                name=jacksink
                client-name=GstSink
                buffer-time={JackClientInput.JACK_BUFFER_TIME_US}
                latency-time={JackClientInput.JACK_LATENCY_TIME_US}
        """

        print(desc)
        print(escape_pipeline_description(desc))
