import typing

from gi.repository import Gst

from digimix.audio.base import AudioMode, GstElement


class SingleJackClientInput(GstElement):
    QUEUE_TIME_NS = 3 * 1000 * 1000 * 1000

    def __init__(self, name: str, conf: typing.Tuple[typing.Tuple[str, AudioMode], ...]):
        self._name = str(name)
        self._conf = conf
        self._src = tuple(f"src-{name}" for name, _ in conf)

        audio_stream_count = 0
        for _, mode in conf:
            audio_stream_count += mode.value

        self._pipeline_description = f"""
        bin.(
            name={self._name}
            jackaudiosrc
                connect=0
                name=jackaudiosrc-{self._name}
                client_name={self._name}
            ! capsfilter
                name=jackaudiosrc_caps-{self._name}
                caps=audio/x-raw,channels={audio_stream_count},channel-mask=(bitmask)0x{'0' * audio_stream_count}
            ! deinterleave
                name=jackaudiosrc_deinter-{self._name}
        """

        i = 0
        for input_name, mode in conf:
            if mode is AudioMode.MONO:
                self._pipeline_description += f"""
                bin.(
                    name={self._name}-{input_name}
                    jackaudiosrc_deinter-{self._name}.src_{i}
                    ! capsfilter
                        name=jackaudiosrc_deinter_caps-{self._name}-src_{i}
                        caps=audio/x-raw,channels=1,channel-mask=0
                    ! queue
                        name=src-{input_name}
                        max-size-time={self.QUEUE_TIME_NS}
                )
                """
                i += 1
            elif mode is AudioMode.STEREO:
                self._pipeline_description += f"""
                bin.(
                    name={self._name}-{input_name}
                    interleave
                        name=jackaudiosrc_inter-{self._name}-{input_name}
                    ! capsfilter
                        name=jackaudiosrc_inter_caps-{self._name}-{input_name}
                        caps=audio/x-raw,channels=2
                    ! queue
                        name=src-{input_name}
                        max-size-time={self.QUEUE_TIME_NS}

                    jackaudiosrc_deinter-{self._name}.src_{i}
                    ! capsfilter
                        name=jackaudiosrc_deinter-{self._name}-src_{i}
                        caps=audio/x-raw,channels=1,channel-mask=(bitmask)0x1
                    ! queue
                        name=jackaudiosrc_pre-inter-{self._name}-{input_name}_0
                        max-size-time={self.QUEUE_TIME_NS}
                    ! jackaudiosrc_inter-{self._name}-{input_name}.sink_0

                    jackaudiosrc_deinter-{self._name}.src_{i + 1}
                    ! capsfilter
                        name=jackaudiosrc_deinter-{self._name}-src_{i + 1}
                        caps=audio/x-raw,channels=1,channel-mask=(bitmask)0x2
                    ! queue
                        name=jackaudiosrc_pre-inter-{self._name}-{input_name}_1
                        max-size-time={self.QUEUE_TIME_NS}
                    ! jackaudiosrc_inter-{self._name}-{input_name}.sink_1
                )
                """
                i += 2
            else:
                raise RuntimeError("Unsupported audio mode: " + str(mode))

        self._pipeline_description += """
        )
        """

    @property
    def name(self) -> str:
        return self._name

    @property
    def sink(self) -> typing.Tuple[str]:
        return tuple()

    @property
    def src(self) -> typing.Tuple[str]:
        return self._src

    @property
    def pipeline_description(self) -> str:
        return self._pipeline_description

    def attach_pipeline(self, pipeline: Gst.Element):
        pass
