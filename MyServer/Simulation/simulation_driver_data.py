import dataclasses

from MyServer.Sensor.Base import SensorDictBase


@dataclasses.dataclass(frozen=True)
class SimulationDriverData[T]:
    sensor: SensorDictBase
    start_value: T
    random_seed: int
    identifier: int
    namespace: str

    def as_dict(self):
        return dataclasses.asdict(self)

