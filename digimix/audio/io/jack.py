import typing
from abc import ABC

from digimix.audio import Gst, GstAudio
from digimix.audio.base import AudioMode
from digimix.audio.io import Input, Output
from digimix.audio.io.jack_fix import get_jack_channel_pos


class JackClient(ABC):
    JACK_BUFFER_TIME_US = 50_000
    JACK_LATENCY_TIME_US = 1_000


class JackClientInput(Input, JackClient, ABC):
    def __init__(self, name: str, conf: typing.Tuple[typing.Tuple[str, AudioMode], ...]):
        super().__init__(name)
        self._conf = conf
        self._src_dict = {name: f"jack-src-{name}" for name, _ in conf}

    @property
    def src(self) -> list[str]:
        return list(self._src_dict.values())

    @property
    def src_dict(self) -> dict[str, str]:
        return self._src_dict

    def attach_pipeline(self, pipeline: Gst.Element):
        pass


class SingleJackClientInput(JackClientInput):
    def __init__(self, name: str, conf: typing.Tuple[typing.Tuple[str, AudioMode], ...]):
        super().__init__(name=name, conf=conf)

        audio_stream_count = 0
        for _, mode in conf:
            audio_stream_count += mode.channels

        self._pipeline_description = f"""
        bin.(
            name=bin-jack-src-{self.name}
            jackaudiosrc
                connect=0
                name=jack-src-{self.name}
                client_name={self.name}
                buffer-time={self.JACK_BUFFER_TIME_US}
                latency-time={self.JACK_LATENCY_TIME_US}
            ! capsfilter
                name=jack-src-caps-{self.name}
                caps=audio/x-raw,channels={audio_stream_count},channel-mask=(bitmask)0x{hex(GstAudio.audio_channel_get_fallback_mask(audio_stream_count))}
            ! deinterleave
                name=jack-src-deinterleave-{self.name}
        """

        i = 0
        for input_name, mode in conf:
            if mode is AudioMode.MONO:
                self._pipeline_description += f"""
                bin.(
                    name=bin-jack-src-in-{self.name}-{input_name}
                    jack-src-deinterleave-{self.name}.src_{get_jack_channel_pos(audio_stream_count, i)}
                    ! capsfilter
                        name=jack-src-deinterleave_caps-{self.name}-{input_name}
                        caps={mode.caps()}
                    ! tee
                        name=jack-src-{input_name}
                )
                """
                i += 1
            elif mode is AudioMode.STEREO:
                self._pipeline_description += f"""
                bin.(
                    name=bin-jack-src-in-{self.name}-{input_name}
                    interleave
                        name=jack-src-interleave-{self.name}-{input_name}
                    ! capsfilter
                        name=jack-src-interleave_caps-{self.name}-{input_name}
                        caps={mode.caps()}
                    ! tee
                        name=jack-src-{input_name}

                    jack-src-deinterleave-{self.name}.src_{get_jack_channel_pos(audio_stream_count, i)}
                    ! capsfilter
                        name=jack-src-deinterleave_caps-{self.name}-{input_name}_left
                        caps={AudioMode.LEFT_ONLY.caps()}
                    ! queue
                        name=queue-jack-src-pre-interleave-{self.name}-{input_name}_left
                        max-size-time={self.QUEUE_TIME_NS}
                    ! jack-src-interleave-{self.name}-{input_name}.sink_0

                    jack-src-deinterleave-{self.name}.src_{get_jack_channel_pos(audio_stream_count, i + 1)}
                    ! capsfilter
                        name=jack-src-deinterleave-{self.name}-{input_name}_right
                        caps={AudioMode.RIGHT_ONLY.caps()}
                    ! queue
                        name=queue-jack-src-pre-interleave-{self.name}-{input_name}_right
                        max-size-time={self.QUEUE_TIME_NS}
                    ! jack-src-interleave-{self.name}-{input_name}.sink_1
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
            name=bin-jack-src-{self.name}
        """

        for input_name, mode in conf:
            if mode is AudioMode.MONO:
                self._pipeline_description += f"""
                bin.(
                    name=bin-jack-src-in-{self.name}-{input_name}
                    jackaudiosrc
                        connect=0
                        name=jack-src-{self.name}-{input_name}
                        client_name={self.name}-{input_name}
                        buffer-time={self.JACK_BUFFER_TIME_US}
                        latency-time={self.JACK_LATENCY_TIME_US}
                    ! capsfilter
                        name=jack-src-caps-{self.name}-{input_name}
                        caps={mode.caps()}
                    ! tee
                        name=jack-src-{input_name}
                )
                """
            elif mode is AudioMode.STEREO:
                self._pipeline_description += f"""
                bin.(
                    name=bin-jack-src-in-{self.name}-{input_name}
                    jackaudiosrc
                        connect=0
                        name=jack-src-{self.name}-{input_name}
                        client_name={self.name}-{input_name}
                        buffer-time={self.JACK_BUFFER_TIME_US}
                        latency-time={self.JACK_LATENCY_TIME_US}
                    ! capsfilter
                        name=jack-src-caps-{self.name}-{input_name}
                        caps={mode.caps()}
                    ! tee
                        name=jack-src-{input_name}
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


class JackClientOutput(Output, JackClient, ABC):
    def __init__(self, name: str, conf: typing.Tuple[typing.Tuple[str, AudioMode], ...]):
        super().__init__(name)
        self._conf = conf
        self._sink_dict = {name: f"jack-sink-{name}" for name, _ in conf}

    @property
    def sink(self) -> list[str]:
        return list(self._sink_dict.values())

    @property
    def sink_dict(self) -> dict[str, str]:
        return self._sink_dict

    def attach_pipeline(self, pipeline: Gst.Pipeline):
        pass


class SingleJackClientOutput(JackClientOutput):
    def __init__(self, name: str, conf: typing.Tuple[typing.Tuple[str, AudioMode], ...]):
        super().__init__(name, conf)

        audio_stream_count = 0
        for _, mode in conf:
            audio_stream_count += mode.channels

        self._pipeline_description = f"""
        bin.(
            name=bin-jack-sink-{self.name}
            interleave
                name=jack-sink-interleave-{self.name}
                channel-positions-from-input=false
            ! capsfilter
                name=jack-sink-caps-{self.name}
                caps=audio/x-raw,channels={audio_stream_count},channel-mask=(bitmask)0x{'0' * audio_stream_count}
            ! jackaudiosink
                connect=0
                name=jack-sink-{self.name}
                client_name={self.name}
                buffer-time={self.JACK_BUFFER_TIME_US}
                latency-time={self.JACK_LATENCY_TIME_US}
        """

        i = 0
        for input_name, mode in conf:
            if mode is AudioMode.MONO:
                self._pipeline_description += f"""
                        bin.(
                            name=bin-jack-sink-{self.name}-{input_name}
                            queue
                                name=jack-sink-{input_name}
                                max-size-time={self.QUEUE_TIME_NS}
                            ! capsfilter
                                name=jack-sink-queue_caps-{input_name}
                                caps={mode.caps()}
                            ! jack-sink-interleave-{self.name}.sink_{i}
                        )
                        """
                i += 1
            elif mode is AudioMode.STEREO:
                self._pipeline_description += f"""
                        bin.(
                            name=bin-jack-sink-{self.name}-{input_name}
                            queue
                                name=jack-sink-{input_name}
                                max-size-time={self.QUEUE_TIME_NS}
                            ! capsfilter
                                name=jack-sink-queue_caps-{input_name}
                                caps={mode.caps()}
                            ! deinterleave
                                name=jack-sink-deinterleave-{input_name}

                            jack-sink-deinterleave-{input_name}.src_0
                            ! capsfilter
                                name=jack-sink-deinterleave_caps-{self.name}-{input_name}_left
                                caps={AudioMode.LEFT_ONLY.caps()}
                            ! queue
                                name=queue-jack-sink-pre-interleave-{self.name}-{input_name}_left
                                max-size-time={self.QUEUE_TIME_NS}
                            ! jack-sink-interleave-{self.name}.sink_{i}

                            jack-sink-deinterleave-{input_name}.src_1
                            ! capsfilter
                                name=jack-sink-deinterleave-{self.name}-{input_name}_right
                                caps={AudioMode.RIGHT_ONLY.caps()}
                            ! queue
                                name=queue-jack-sink-pre-interleave-{self.name}-{input_name}_right
                                max-size-time={self.QUEUE_TIME_NS}
                            ! jack-sink-interleave-{self.name}.sink_{i + 1}
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
