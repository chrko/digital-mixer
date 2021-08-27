import typing
from abc import ABC

from gi.repository import Gst

from digimix.audio.base import AudioMode, GstElement


class JackClientInput(GstElement, ABC):
    QUEUE_TIME_NS = 3 * 1000 * 1000 * 1000

    def __init__(self, name: str, conf: typing.Tuple[typing.Tuple[str, AudioMode], ...]):
        self._name = str(name)
        self._conf = conf
        self._src = [f"jas-src-{name}" for name, _ in conf]

    @property
    def name(self) -> str:
        return self._name

    @property
    def sink(self) -> list[str]:
        return []

    @property
    def src(self) -> list[str]:
        return self._src

    def attach_pipeline(self, pipeline: Gst.Element):
        pass


class SingleJackClientInput(JackClientInput):
    def __init__(self, name: str, conf: typing.Tuple[typing.Tuple[str, AudioMode], ...]):
        super().__init__(name=name, conf=conf)

        audio_stream_count = 0
        for _, mode in conf:
            audio_stream_count += mode.value

        self._pipeline_description = f"""
        bin.(
            name=bin-{self._name}
            jackaudiosrc
                connect=0
                name=jas-{self._name}
                client_name={self._name}
            ! capsfilter
                name=jas-caps-{self._name}
                caps=audio/x-raw,channels={audio_stream_count},channel-mask=(bitmask)0x{'0' * audio_stream_count}
            ! deinterleave
                name=jas-deinter-{self._name}
        """

        i = 0
        for input_name, mode in conf:
            if mode is AudioMode.MONO:
                self._pipeline_description += f"""
                bin.(
                    name=jas-in-bin-{self._name}-{input_name}
                    jas-deinter-{self._name}.src_{i}
                    ! capsfilter
                        name=jas-deinter_caps-{self._name}-src_{i}
                        caps=audio/x-raw,channels=1,channel-mask=(bitmask)0x0
                    ! tee
                        name=jas-src-{input_name}
                )
                """
                i += 1
            elif mode is AudioMode.STEREO:
                self._pipeline_description += f"""
                bin.(
                    name=jas-in-bin-{self._name}-{input_name}
                    interleave
                        name=jas-inter-{self._name}-{input_name}
                    ! capsfilter
                        name=jas-inter_caps-{self._name}-{input_name}
                        caps=audio/x-raw,channels=2,channel-mask=(bitmask)0x3
                    ! tee
                        name=jas-src-{input_name}

                    jas-deinter-{self._name}.src_{i}
                    ! capsfilter
                        name=jas-deinter_caps-{self._name}-src_{i}
                        caps=audio/x-raw,channels=1,channel-mask=(bitmask)0x1
                    ! queue
                        name=queue-jas-pre-inter-{self._name}-{input_name}_0
                        max-size-time={self.QUEUE_TIME_NS}
                    ! jas-inter-{self._name}-{input_name}.sink_0

                    jas-deinter-{self._name}.src_{i + 1}
                    ! capsfilter
                        name=jas-deinter-{self._name}-src_{i + 1}
                        caps=audio/x-raw,channels=1,channel-mask=(bitmask)0x2
                    ! queue
                        name=queue-jas-pre-inter-{self._name}-{input_name}_1
                        max-size-time={self.QUEUE_TIME_NS}
                    ! jas-inter-{self._name}-{input_name}.sink_1
                )
                """
                i += 2
            else:
                raise RuntimeError("Unsupported audio mode: " + str(mode))

        self._pipeline_description += """
        )
        """

    @property
    def pipeline_description(self) -> str:
        return self._pipeline_description


class MultiJackClientInput(JackClientInput):
    def __init__(self, name: str, conf: typing.Tuple[typing.Tuple[str, AudioMode], ...]):
        super().__init__(name, conf)

        self._pipeline_description = f"""
        bin.(
            name={self._name}
        """

        for input_name, mode in conf:
            if mode is AudioMode.MONO:
                self._pipeline_description += f"""
                bin.(
                    name=jas-bin-{self._name}-{input_name}
                    jackaudiosrc
                        connect=0
                        name=jas-{self._name}-{input_name}
                        client_name={self._name}-{input_name}
                    ! capsfilter
                        name=jas-caps-{self._name}-{input_name}
                        caps=audio/x-raw,channels=1,channel-mask=(bitmask)0x0
                    ! tee
                        name=jas-src-{input_name}
                )
                """
            elif mode is AudioMode.STEREO:
                self._pipeline_description += f"""
                bin.(
                    name=jas-bin-{self._name}-{input_name}
                    jackaudiosrc
                        connect=0
                        name=jas-{self._name}-{input_name}
                        client_name={self._name}-{input_name}
                    ! capsfilter
                        name=jas-caps-{self._name}-{input_name}
                        caps=audio/x-raw,channels=2,channel-mask=(bitmask)0x3
                    ! tee
                        name=jas-src-{input_name}
                )
                """
            else:
                raise RuntimeError("Unsupported audio mode: " + str(mode))

        self._pipeline_description += """
        )
        """

    @property
    def pipeline_description(self) -> str:
        return self._pipeline_description
