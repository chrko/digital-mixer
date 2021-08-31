from digimix.audio import Gst
from digimix.audio.base import GstElement


class MasterBus(GstElement):
    QUEUE_TIME_NS = 3 * 1000 * 1000 * 1000

    def __init__(self, name: str, inputs: list[str]):
        self._name = str(name)
        self._inputs = list(inputs)

    @property
    def name(self):
        return self._name

    @property
    def src(self) -> list[str]:
        return [f"master-src-{self._name}"]

    @property
    def sink(self) -> list[str]:
        return []

    def attach_pipeline(self, pipeline: Gst.Pipeline):
        pass

    @property
    def pipeline_description(self) -> str:
        desc = f"""
        bin.(
            name=bin-master-bus-{self._name}
            audiomixer
                name=master-bus-mixer-{self._name}
            ! queue
                name=queue-master-bus-mixer-{self._name}
                max-size-time={self.QUEUE_TIME_NS}
            ! tee
                name=master-src-{self._name}
        """

        for input_name in self._inputs:
            desc += f"""
            {input_name}.
            ! queue
                name=queue-master-bux-mixer-{self._name}-{input_name}
                max-size-time={self.QUEUE_TIME_NS}
            ! master-bus-mixer-{self._name}.
            """

        desc += """
        )
        """
        return desc
