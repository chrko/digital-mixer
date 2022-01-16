from digimix.audio import Gst
from digimix.audio.base import GstElement


class MasterBus(GstElement):
    def __init__(self, name: str, inputs: list[str]):
        super().__init__(name)
        self._inputs = list(inputs)

    @property
    def src(self) -> list[str]:
        return [f"master-src-{self.name}"]

    @property
    def sink(self) -> list[str]:
        return []

    def attach_pipeline(self, pipeline: Gst.Pipeline):
        pass

    @property
    def pipeline_description(self) -> str:
        desc = f"""
        bin.(
            name=bin-master-bus-{self.name}
            audiomixer
                name=master-bus-mixer-{self.name}
            ! queue
                name=queue-master-bus-mixer-{self.name}
                max-size-time={self.QUEUE_TIME_NS}
            ! tee
                name=master-src-{self.name}
        """

        for input_name in self._inputs:
            desc += f"""
            {input_name}.
            ! queue
                name=queue-master-bux-mixer-{self.name}-{input_name}
                max-size-time={self.QUEUE_TIME_NS}
            ! master-bus-mixer-{self.name}.
            """

        desc += """
        )
        """
        return desc
