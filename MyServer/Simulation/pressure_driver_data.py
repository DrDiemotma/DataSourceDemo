import dataclasses
from .simulation_driver_data import SimulationDriverData


@dataclasses.dataclass(frozen=True)
class PressureDriverData(SimulationDriverData[float]):
    st_dev: float
    st_dev_broken: float
    value_idle: float
    value_running: float
    value_running_broken: float
    adaption_rate: float