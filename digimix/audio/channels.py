import enum
import typing

from digimix.audio import Gst
from digimix.audio.base import GstElement
from digimix.audio.utils import amplitude_to_db, db_to_amplitude


@enum.unique
class AudioPanoramaMethods(enum.IntEnum):
    PSYCHOACOUSTIC = 0
    SIMPLE = 1


class FaderChannel(GstElement):
    def __init__(
        self,
        name: str,
        gain_db: float = 0,
        phase_invert: bool = False,
        pan: float = 0,
        pan_method: AudioPanoramaMethods = AudioPanoramaMethods.PSYCHOACOUSTIC,
    ):
        super().__init__(name)

        self._pipeline: typing.Optional[Gst.Pipeline] = None
        self._fader: typing.Optional[Gst.Element] = None

        self._phase_invert = bool(phase_invert)
        self._gain_db = float(gain_db)

        self._pan: float = 0.0
        self.pan = pan

        self._pan_method: AudioPanoramaMethods = AudioPanoramaMethods.PSYCHOACOUSTIC
        self.pan_method = pan_method

        self._fader_db: float = 0.0
        self._cut: bool = False

    @property
    def gain_db(self) -> float:
        return self._gain_db

    @gain_db.setter
    def gain_db(self, new_gain_db: float):
        new_gain_db = float(new_gain_db)
        self._gain_db = new_gain_db
        if self._pipeline is not None:
            gain = self._pipeline.get_by_name(f"fader_channel-gain-{self.name}")  # type: Gst.Element
            gain.set_property("amplification", self.gain_amplitude)

    @property
    def gain_amplitude(self) -> float:
        return db_to_amplitude(self._gain_db)

    @gain_amplitude.setter
    def gain_amplitude(self, new_gain_amplitude: float):
        self.gain_db = amplitude_to_db(new_gain_amplitude)

    @property
    def pan(self) -> float:
        return self._pan

    @pan.setter
    def pan(self, new_pan: float):
        if not -1.0 <= new_pan <= 1.0:
            raise ValueError(f"pan must be between [-1, 1]. Given {new_pan}")
        self._pan = new_pan
        if self._pipeline is not None:
            panorama = self._pipeline.get_by_name(f"fader_channel-pan-{self.name}")  # type: Gst.Element
            panorama.set_property("panorama", self._pan)

    @property
    def pan_method(self) -> AudioPanoramaMethods:
        return self._pan_method

    @pan_method.setter
    def pan_method(self, new_pan_method: AudioPanoramaMethods):
        if new_pan_method not in AudioPanoramaMethods:
            raise ValueError(f"Given pan_method is not a supported AudioPanoramaMethods: {new_pan_method}")
        self._pan_method = new_pan_method
        if self._pipeline is not None:
            panorama = self._pipeline.get_by_name(f"fader_channel-pan-{self.name}")  # type: Gst.Element
            panorama.set_property("method", int(self._pan_method))

    @property
    def fader_db(self) -> float:
        return self._fader_db

    @fader_db.setter
    def fader_db(self, new_fader_db: float):
        self._fader_db = float(new_fader_db)
        if self._fader is not None:
            self._fader.set_property("volume", self.fader_amplitude)

    @property
    def fader_amplitude(self) -> float:
        return db_to_amplitude(self._fader_db)

    @fader_amplitude.setter
    def fader_amplitude(self, new_fader_amplitude: float):
        self.fader_db = amplitude_to_db(new_fader_amplitude)

    @property
    def cut(self) -> bool:
        return self._cut

    @cut.setter
    def cut(self, new_cut: bool):
        new_cut = bool(new_cut)
        self._fader.set_property("mute", new_cut)

    @property
    def pipeline_description(self) -> str:
        desc = f"""
        bin.(
            name=bin-fader_channel-{self.name}
            queue
                name=fader_channel-sink-{self.name}
            ! audioamplify
                name=fader_channel-gain-{self.name}
                amplification={self.gain_amplitude}"""

        if self._phase_invert:
            desc += f"""
            ! audioinvert
                name=fader_channel-phase_invert-{self.name}"""

        desc += f"""
            ! tee
                name=fader_channel-pre_fader-{self.name}
            ! level
                name=fader_channel-level-{self.name}
            ! volume
                name=fader_channel-fader-{self.name}
            ! tee
                name=fader_channel-post_fader-{self.name}
            ! audiopanorama
                name=fader_channel-pan-{self.name}
                panorama={self._pan}
                method={self._pan_method}
            ! capsfilter
                name=fader_channel-pan_caps-{self.name}
                caps=audio/x-raw,channels=2,channel-mask=(bitmask)0x3
            ! tee
                name=fader_channel-src-{self.name}
        )"""

        return desc

    def attach_pipeline(self, pipeline: Gst.Pipeline):
        self._pipeline = pipeline
        self._fader = pipeline.get_by_name(f"fader_channel-fader-{self.name}")

    @property
    def sink(self) -> list[str]:
        return [f"fader_channel-sink-{self.name}"]

    @property
    def src(self) -> list[str]:
        return [f"fader_channel-src-{self.name}"]

    @property
    def phase_invert(self) -> bool:
        return self._phase_invert
