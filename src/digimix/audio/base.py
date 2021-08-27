import enum
import typing
from abc import ABC, abstractmethod

from digimix.audio.gstreamer import Gst
from digimix.audio.utils import amplitude_to_db, db_to_amplitude


class GStreamer(ABC):
    @property
    @abstractmethod
    def pipeline_description(self) -> str:
        ...

    @abstractmethod
    def attach_pipeline(self, pipeline: Gst.Pipeline):
        ...


class GstElement(GStreamer):
    @property
    @abstractmethod
    def sink(self) -> typing.Tuple[str]:
        ...

    @property
    @abstractmethod
    def src(self) -> typing.Tuple[str]:
        ...


@enum.unique
class AudioMode(enum.Enum):
    MONO = 1
    STEREO = 2


class InputPatchPanel(GstElement):
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
                        name=jack_src-{input_name}
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
                        name=jack_src-{input_name}
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


class Stereo2Mono(GstElement):
    QUEUE_TIME_NS = 3 * 1000 * 1000 * 1000

    def __init__(self, name: str, *, level_db: float = None, level_amplitude: float = None):
        self._name = str(name)

        self._sink = f"stereo2mono_sink-{name}"
        self._src = f"stereo2mono_src-{name}"

        if level_db is not None:
            if level_amplitude is not None:
                raise AssertionError(f"{self.__class__.__name__} only supports level_db OR level_amplitude")
            self._level_db = level_db
        elif level_amplitude is not None:
            self._level_db = amplitude_to_db(level_amplitude)
        else:
            self._level_db = 0

        self._pipeline: typing.Optional[Gst.Pipeline] = None
        self._volume_element: typing.Optional[Gst.Element] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def sink(self) -> typing.Tuple[str]:
        return tuple(self._sink)

    @property
    def src(self) -> typing.Tuple[str]:
        return tuple(self._src)

    @property
    def level_db(self) -> float:
        return self._level_db

    @level_db.setter
    def level_db(self, new_value: float):
        old_value = self._level_db
        if old_value != new_value:
            self._level_db = float(new_value)
            if self._volume_element:
                self._volume_element.set_property("volume", db_to_amplitude(new_value))

    @property
    def level_amplitude(self) -> float:
        return db_to_amplitude(self._level_db)

    @level_amplitude.setter
    def level_amplitude(self, new_value: float):
        old_value = db_to_amplitude(self._level_db)
        if old_value != new_value:
            self._level_db = amplitude_to_db(new_value)
            if self._volume_element:
                self._volume_element.set_property("volume", new_value)

    @property
    def pipeline_description(self) -> str:
        return f"""
        bin.(
            name=stereo2mono-{self.name}
            queue
                name=stereo2mono_sink-{self.name}
                max-size-time={self.QUEUE_TIME_NS}
            ! audio/x-raw,channels=2
            ! deinterleave
                name=stereo2mono_split-{self.name}
            audiomixer
                name=mono_summer-{self.name}
            ! volume
                name=mono_sum_volume_adjust-{self.name}
                volume={db_to_amplitude(self._level_db)}
            ! audio/x-raw,channels=1
            ! queue
                name=stereo2mono_src_queue-{self.name}
                max-size-time={self.QUEUE_TIME_NS}
            ! tee
                name=stereo2mono_src-{self.name}
            stereo2mono_split-{self.name}.src_0,src_1 ! mono_summer-{self.name}.sink_0,sink_1
        )
        """

    def attach_pipeline(self, pipeline: Gst.Pipeline):
        if self._pipeline is not None:
            self._pipeline = pipeline
            if pipeline is not None:
                self._volume_element = pipeline.get_by_name(f"mono_sum_volume_adjust-{self.name}")
        else:
            raise RuntimeError("Multiple invocation of attach_pipeline not supported")
