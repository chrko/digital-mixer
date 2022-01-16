import typing

from digimix.audio import Gst
from digimix.audio.base import AudioMode
from digimix.audio.io import Input, Output


class PipewireInput(Input):
    def __init__(self, name: str, conf: typing.Tuple[typing.Tuple[str, AudioMode], ...]):
        super().__init__(name)
        self._conf = conf
        self._src = [f"pipewire-src-{name}" for name, _ in conf]

        self._pipeline_description = f"""
        bin.(
            name=bin-pipewire-src-{self.name}
        """

        for input_name, mode in conf:
            if mode is AudioMode.MONO:
                self._pipeline_description += f"""
                bin.(
                    name=bin-pipewire-src-in-{self.name}-{input_name}
                    pipewiresrc
                        name=pipewire-src-{self.name}-{input_name}
                        client_name={self.name}-{input_name}
                    ! capsfilter
                        name=pipewire-src-caps-{self.name}-{input_name}
                        caps={mode.caps()}
                    ! tee
                        name=pipewire-src-{input_name}
                )
                """
            elif mode is AudioMode.STEREO:
                self._pipeline_description += f"""
                bin.(
                    name=bin-pipewire-src-in-{self.name}-{input_name}
                    pipewiresrc
                        name=pipewire-src-{self.name}-{input_name}
                        client_name={self.name}-{input_name}
                    ! capsfilter
                        name=pipewire-src-caps-{self.name}-{input_name}
                        caps={mode.caps()}
                    ! tee
                        name=pipewire-src-{input_name}
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

    @property
    def src(self) -> list[str]:
        return self._src

    def attach_pipeline(self, pipeline: Gst.Element):
        pass


class PipewireOutput(Output):
    def __init__(self, name: str, conf: typing.Tuple[typing.Tuple[str, AudioMode], ...]):
        super().__init__(name)
        self._conf = conf
        self._sink = [f"pipewire-sink-{name}" for name, _ in conf]

        audio_stream_count = 0
        for _, mode in conf:
            audio_stream_count += mode.channels

        self._pipeline_description = f"""
        bin.(
            name=bin-pipewire-sink-{self.name}
            interleave
                name=pipewire-sink-interleave-{self.name}
                channel-positions-from-input=false
            ! capsfilter
                name=pipewire-sink-caps-{self.name}
                caps=audio/x-raw,channels={audio_stream_count},channel-mask=(bitmask)0x{'0' * audio_stream_count}
            ! pipewiresink
                name=pipewire-sink-{self.name}
                client_name={self.name}
        """

        i = 0
        for input_name, mode in conf:
            if mode is AudioMode.MONO:
                self._pipeline_description += f"""
                        bin.(
                            name=bin-pipewire-sink-{self.name}-{input_name}
                            queue
                                name=pipewire-sink-{input_name}
                                max-size-time={self.QUEUE_TIME_NS}
                            ! capsfilter
                                name=pipewire-sink-queue_caps-{input_name}
                                caps={mode.caps()}
                            ! pipewire-sink-interleave-{self.name}.sink_{i}
                        )
                        """
                i += 1
            elif mode is AudioMode.STEREO:
                self._pipeline_description += f"""
                        bin.(
                            name=bin-pipewire-sink-{self.name}-{input_name}
                            queue
                                name=pipewire-sink-{input_name}
                                max-size-time={self.QUEUE_TIME_NS}
                            ! capsfilter
                                name=pipewire-sink-queue_caps-{input_name}
                                caps={mode.caps()}
                            ! deinterleave
                                name=pipewire-sink-deinterleave-{input_name}

                            pipewire-sink-deinterleave-{input_name}.src_0
                            ! capsfilter
                                name=pipewire-sink-deinterleave_caps-{self.name}-{input_name}_left
                                caps={AudioMode.LEFT_ONLY.caps()}
                            ! queue
                                name=queue-pipewire-sink-pre-interleave-{self.name}-{input_name}_left
                                max-size-time={self.QUEUE_TIME_NS}
                            ! pipewire-sink-interleave-{self.name}.sink_{i}

                            pipewire-sink-deinterleave-{input_name}.src_1
                            ! capsfilter
                                name=pipewire-sink-deinterleave-{self.name}-{input_name}_right
                                caps={AudioMode.RIGHT_ONLY.caps()}
                            ! queue
                                name=queue-pipewire-sink-pre-interleave-{self.name}-{input_name}_right
                                max-size-time={self.QUEUE_TIME_NS}
                            ! pipewire-sink-interleave-{self.name}.sink_{i + 1}
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

    @property
    def sink(self) -> list[str]:
        return self._sink

    def attach_pipeline(self, pipeline: Gst.Pipeline):
        pass
