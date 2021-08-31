from abc import ABC

from digimix.audio.base import GstElement


class Input(GstElement, ABC):
    @property
    def sink(self) -> list[str]:
        return []


class Output(GstElement, ABC):
    @property
    def src(self) -> list[str]:
        return []
