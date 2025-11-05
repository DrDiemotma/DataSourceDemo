import dataclasses
from .simulation_driver_data import SimulationDriverData


@dataclasses.dataclass(frozen=True)
class TemperatureDriverData(SimulationDriverData[float]):
    st_dev: float
    value_idle: float
    value_running: float
    value_running_broken: float
    adaption_rate: float

    def as_dict(self):
        return dataclasses.asdict(self)
