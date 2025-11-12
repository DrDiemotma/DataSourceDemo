import json
from datetime import datetime

from MyServer.MachineOperation import State, Mode
from abc import ABC, abstractmethod

from .simulation_driver_data import SimulationDriverData
from MyServer.Sensor.Base import SensorBase, SensorDictBase


class SimulationDriver[T](ABC):
    """
    Mutator class for data, depending on state and operation mode of the machine.
    """
    def __init__(self, sensor: SensorBase[T], start_value: T, mode: Mode = Mode.IDLE, state: State = State.NORMAL):
        self.__sensor: SensorBase[T] = sensor
        self.__sensor.source = self.measure
        self.__current_value: T = start_value
        self.__value_time: datetime = datetime.now()
        self.__mode: Mode = mode
        self.__state: State = state
        sensor.driver_dict_callback = self.to_driver_data

    @property
    def sensor(self):
        """Get the sensor assigned to the simulated driver."""
        return self.__sensor

    @property
    def mode(self) -> Mode:
        """Get the currently set mode."""
        return self.__mode

    @mode.setter
    def mode(self, mode: Mode):
        """Set the mode."""
        self.__mode = mode

    @property
    def state(self):
        """Get the state of the machine."""
        return self.__state

    @state.setter
    def state(self, state: State):
        """Set the state."""
        self.__state = state

    @property
    def last_value(self) -> T:
        """Get the last measured value."""
        return self.__current_value

    @property
    def last_value_time(self) -> datetime:
        """Get the time of the last measurement."""
        return self.__value_time

    @abstractmethod
    def to_driver_data(self) -> SimulationDriverData:
        """Translate the data to a serializable json."""
        pass

    @abstractmethod
    def _update_current_value(self) -> tuple[datetime, T]:
        """Update the current value."""
        pass

    def measure(self) -> T:
        """Interface function for measurements."""
        self.__value_time, self.__current_value = self._update_current_value()
        return self.__current_value


class DriverFactory[T](ABC):
    @staticmethod
    @abstractmethod
    def from_dict(d: dict) -> SimulationDriver[T]:
        """create a new instance from a dict."""
        ...
