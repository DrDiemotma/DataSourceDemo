import json
import math
import random
from datetime import datetime

from MyServer.MachineOperation import State, Mode
from MyServer.Sensor import PressureSensor
from MyServer.Sensor.Base import SensorDictBase
from MyServer.Simulation.simulation_driver import SimulationDriver, SimulationDriverData, DriverFactory
from MyServer.Simulation.pressure_driver_data import PressureDriverData


class PressureSimulationDriver(SimulationDriver[float]):
    def __init__(self, sensor: PressureSensor,
                 start_value: float = 1013.0,
                 random_seed: int = 42,
                 st_dev: float = 0.04,
                 st_dev_broken: float = 0.4,
                 value_idle: float = 1013.0,
                 value_running: float = 255.0,
                 value_running_broken: float = 866.0,
                 adaption_rate: float = 0.01):
        super().__init__(sensor, start_value)
        self._seed = random_seed
        self._random = random.Random(random_seed)
        self._st_dev = st_dev
        self._st_dev_broken = st_dev_broken
        self._value_idle = value_idle
        self._value_running = value_running
        self._value_running_broken = value_running_broken
        self._adaption_rate = adaption_rate


    def to_driver_data(self) -> SimulationDriverData[float]:
        sensor_description: SensorDictBase = self.sensor.to_data_object()
        d: PressureDriverData = PressureDriverData(
            identifier=self.sensor.identifier,
            namespace=self.sensor.namespace,
            start_value=self.last_value,
            random_seed=self._seed,
            value_idle=self._value_idle,
            value_running=self._value_running,
            adaption_rate=self._adaption_rate,
            st_dev=self._st_dev,
            st_dev_broken=self._st_dev_broken,
            sensor=sensor_description,
            value_running_broken=self._value_running_broken
        )
        return d

    def _update_current_value(self) -> tuple[datetime, float]:
        target_value, st_dev = self._target_value()
        time_delta = (datetime.now() - self.last_value_time).total_seconds()
        weight = math.exp(- time_delta / self._adaption_rate)
        adapted_value = weight * self.last_value + (1 - weight) * target_value
        noisy_value = self._random.normalvariate(adapted_value, st_dev)
        time_stamp = datetime.now()
        return time_stamp, noisy_value

    def _target_value(self) -> tuple[float, float]:
        match self.state:
            case State.NORMAL:
                return self._target_value_healthy()
            case State.BROKEN:
                return self._target_value_broken()
        return 0, 0

    def _target_value_healthy(self) -> tuple[float, float]:
        match self.mode:
            case Mode.IDLE:
                return self._value_idle, self._st_dev
            case Mode.RUNNING:
                return self._value_running, self._st_dev

    def _target_value_broken(self) -> tuple[float, float]:
        match self.mode:
            case Mode.IDLE:
                return self._value_idle, self._st_dev
            case Mode.RUNNING:
                return self._value_running_broken, self._st_dev_broken

class PressureSimulationDriverFactory(DriverFactory[float]):

    @staticmethod
    def from_dict(d: dict) -> SimulationDriver[float]:
        if not "sensor" in d:
            raise ValueError("Dict is not in the right format.")
        sensor_dict = d.get("sensor")
        try:
            sensor_data = SensorDictBase(**sensor_dict)
        except:
            raise  # some fields mismatch here, we implement special catches later

        sensor = PressureSensor(sensor_data.identifier,
                                namespace=sensor_data.namespace,
                                updates_per_second=sensor_data.updates_per_second)

        driver = PressureSimulationDriver(sensor=sensor,
                                          start_value=d["start_value"],
                                          random_seed=d["random_seed"],
                                          st_dev = d["st_dev"],
                                          st_dev_broken = d["st_dev_broken"],
                                          value_idle = d["value_idle"],
                                          value_running = d["value_running"],
                                          value_running_broken = d["value_running_broken"],
                                          adaption_rate = d["adaption_rate"]
                                          )