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
            ! audio/x-raw,channels=2,channel-mask=(bitmask)0x3
            ! deinterleave
                name=stereo2mono_split-{self.name}
            audiomixer
                name=stereo2mono_mix-{self.name}
            ! volume
                name=stereo2mono_volume-{self.name}
                volume={db_to_amplitude(self._level_db)}
            ! audio/x-raw,channels=1,channel-mask=(bitmask)0x0
            ! tee
                name=stereo2mono_src-{self.name}
            stereo2mono_split-{self.name}.src_0,src_1 ! stereo2mono_mix-{self.name}.sink_0,sink_1
        )
        """

    def attach_pipeline(self, pipeline: Gst.Pipeline):
        if self._pipeline is not None:
            self._pipeline = pipeline
            if pipeline is not None:
                self._volume_element = pipeline.get_by_name(f"stereo2mono_volume-{self.name}")
        else:
            raise RuntimeError("Multiple invocation of attach_pipeline not supported")
