import json
from datetime import datetime

from MyServer.Sensor import PressureSensor
from MyServer.Simulation.simulation_driver import SimulationDriver, SimulationDriverData, DriverFactory


class PressureSimulationDriver(SimulationDriver[float]):
    def __init__(self, sensor: PressureSensor, start_value: float = 1013.0, random_seed: int = 42):
        super().__init__(sensor, start_value)
        self._seed = random_seed


    def to_driver_data(self) -> SimulationDriverData:
        raise NotImplementedError()

    def _update_current_value(self) -> tuple[datetime, float]:
        raise NotImplementedError()

class PressureSimulationDriverFactory(DriverFactory[float]):

    @staticmethod
    def from_dict(d: dict) -> SimulationDriver[float]:
        raise NotImplementedError()