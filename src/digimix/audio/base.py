import enum
import typing
from abc import ABC, abstractmethod

from digimix.audio import Gst, GstAudio
from digimix.audio.utils import amplitude_to_db, db_to_amplitude


class GstElement(ABC):
    QUEUE_TIME_NS = 3 * 1000 * 1000 * 1000

    def __init__(self, name: str):
        self.__name = str(name)

    @property
    def name(self) -> str:
        return self.__name

    @property
    @abstractmethod
    def sink(self) -> list[str]:
        ...

    @property
    @abstractmethod
    def src(self) -> list[str]:
        ...

    @property
    @abstractmethod
    def pipeline_description(self) -> str:
        ...

    @abstractmethod
    def attach_pipeline(self, pipeline: Gst.Pipeline):
        ...


@enum.unique
class AudioMode(enum.Enum):
    UNKNOWN = (1, [GstAudio.AudioChannelPosition.NONE])
    MONO = (1, [GstAudio.AudioChannelPosition.MONO])
    STEREO = (2, [GstAudio.AudioChannelPosition.FRONT_LEFT, GstAudio.AudioChannelPosition.FRONT_RIGHT])
    LEFT_ONLY = (1, [GstAudio.AudioChannelPosition.FRONT_LEFT])
    RIGHT_ONLY = (1, [GstAudio.AudioChannelPosition.FRONT_RIGHT])

    def __init__(self, channels, channel_positions):
        self._channels = int(channels)
        valid, mask = GstAudio.audio_channel_positions_to_mask(channel_positions, True)
        if not valid:
            raise AssertionError("Couldn't convert to channel mask")
        self._channel_mask = f"{mask:x}"

    @property
    def channels(self) -> int:
        return self._channels

    @property
    def channel_mask(self) -> str:
        return self._channel_mask

    def caps(self, format_info="audio/x-raw"):
        return f"{format_info},channels={self.channels},channel-mask=(bitmask)0x{self.channel_mask}"


class Stereo2Mono(GstElement):
    def __init__(self, name: str, *, level_db: float = None, level_amplitude: float = None):
        super().__init__(name)

        self._sink = f"stereo2mono-sink-{self.name}"
        self._src = f"stereo2mono-src-{self.name}"

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
    def sink(self) -> list[str]:
        return [self._sink]

    @property
    def src(self) -> list[str]:
        return [self._src]

    @property
    def level_db(self) -> float:
        return self._level_db

    @level_db.setter
    def level_db(self, new_level_db: float):
        new_level_db = float(new_level_db)
        self._level_db = new_level_db
        if self._volume_element:
            self._volume_element.set_property("volume", db_to_amplitude(new_level_db))

    @property
    def level_amplitude(self) -> float:
        return db_to_amplitude(self._level_db)

    @level_amplitude.setter
    def level_amplitude(self, new_level_amplitude: float):
        self.level_db = amplitude_to_db(new_level_amplitude)

    @property
    def pipeline_description(self) -> str:
        return f"""
        bin.(
            name=bin-stereo2mono-{self.name}
            queue
                name=stereo2mono-sink-{self.name}
                max-size-time={self.QUEUE_TIME_NS}
            ! audio/x-raw,channels=2,channel-mask=(bitmask)0x3
            ! deinterleave
                name=stereo2mono-split-{self.name}
            audiomixer
                name=stereo2mono-mix-{self.name}
            ! volume
                name=stereo2mono-volume-{self.name}
                volume={db_to_amplitude(self._level_db)}
            ! audio/x-raw,channels=1,channel-mask=(bitmask)0x0
            ! tee
                name=stereo2mono-src-{self.name}
            stereo2mono-split-{self.name}.src_0,src_1 ! stereo2mono-mix-{self.name}.sink_0,sink_1
        )
        """

    def attach_pipeline(self, pipeline: Gst.Pipeline):
        if self._pipeline is not None:
            self._pipeline = pipeline
            if pipeline is not None:
                self._volume_element = pipeline.get_by_name(f"stereo2mono-volume-{self.name}")
        else:
            raise RuntimeError("Multiple invocation of attach_pipeline not supported")
