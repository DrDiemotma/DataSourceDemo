import json
from typing import Any
import logging
import dataclasses
from enum import Enum

from MyServer.Lifetime.machine_model_base import MachineModelBase
from MyServer.MachineOperation.sensor_data_model import SensorId
from MyServer.MachineOperation import State, Mode, SensorType
from MyServer.Sensor import TemperatureSensor, PressureSensor
from MyServer.Simulation import DriverFactory, TemperatureSimulationDriverFactory, TemperatureSimulationDriver, \
    SimulationDriver, PressureSimulationDriver
from MyServer.Sensor.Base import SensorBase, DriverBase

MACHINE_STATE: str = "machine_state"


class MachineModel(MachineModelBase):
    """Model for machine simulation. Handles the machine state and mode."""

    def custom_message(self, message: dict[str, Any]) -> bool:
        logging.debug("Received message.")
        d_used = {x: False for x in message.keys()}
        if MACHINE_STATE in message:
            set_state: bool = message[MACHINE_STATE]
            logging.debug(f"Set machine state \"running\": {set_state}.")
            if set_state:
                self.set_state_normal()
                d_used[MACHINE_STATE] = True
            else:
                self.set_state_broken()
                d_used[MACHINE_STATE] = True

        # find any element that has not been processed
        fully_used = all(d_used.values())
        if not fully_used:
            logging.warning(f"Unused message(s): {",".join([k for k, v in d_used.items() if not v])}")
        return fully_used


    def start_job(self):
        logging.info("Starting job.")
        for mutator in self._drivers:
            mutator.mode = Mode.RUNNING

    def stop_job(self):
        logging.info("Stopping job.")
        for mutator in self._drivers:
            mutator.mode = Mode.IDLE

    def set_state_broken(self):
        logging.info("Setting machine state to \"broken\".")
        for mutator in self._drivers:
            mutator.state = State.BROKEN

    def set_state_normal(self):
        logging.info("Setting machine state to \"normal\".")
        for mutator in self._drivers:
            mutator.state = State.NORMAL

    def __init__(self):
        self._sensors: list[SensorBase] = []
        self._drivers: list[DriverBase | SimulationDriver] = []
        self._state: State = State.NORMAL
        self._mode: Mode = Mode.RUNNING

        self._sensor_factory_map: dict[SensorType, DriverFactory] = {
            SensorType.TEMPERATURE: TemperatureSimulationDriverFactory(),
        }

    def __del__(self):
        for sensor in self._sensors:
            sensor.stop()

    def add_sensor(self, sensor: SensorBase, driver: DriverBase | SimulationDriver = None, **kwargs):
        """
        Add a sensor.
        :param sensor: Sensor to add.
        :param driver: mutator for the sensor. If None, a default mutator is created for the respective sensor.
        """
        logging.info(f"Adding sensor {sensor.name}, type {sensor.sensor_type}, to machine.")
        self._sensors.append(sensor)
        if driver is not None:
            logging.info(f"Driver for sensor {sensor.name} given, continue with present one.")
            driver.state = self._state
            driver.mode = self._mode
            self._drivers.append(driver)
            return

        logging.info(f"No driver for sensor {sensor.name} given, use default configuration.")
        # create the driver automatically
        if isinstance(sensor, TemperatureSensor):
            logging.info(f"Adding {sensor.name} as temperature sensor.")
            temperature_driver: TemperatureSimulationDriver = TemperatureSimulationDriver(sensor, **kwargs)
            temperature_driver.state = self._state
            temperature_driver.mode = self._mode
            self._drivers.append(temperature_driver)
        elif isinstance(sensor, PressureSensor):
            logging.info(f"Adding {sensor.name} as pressure sensor.")
            pressure_driver: PressureSimulationDriver = PressureSimulationDriver(sensor, **kwargs)
            pressure_driver.state = self._state
            pressure_driver.mode = self._mode
            self._drivers.append(pressure_driver)

    @property
    def mutators(self) -> list[DriverBase]:
        """Get a list of current mutators to fine-tune behaviour."""
        return list(self._drivers)

    @property
    def sensors(self) -> list[SensorBase]:
        """Get the sensors"""
        return [x.sensor for x in self._drivers]


    def save_configuration(self, file_path: str):
        """Save the current configuration to a file."""
        logging.info(f"Saving configuration to file {file_path}.")
        serialized = []
        for driver in self._drivers:
            d = driver.to_driver_data()
            sensor_type = d.sensor.sensor_type
            encoder = self._sensor_factory_map[sensor_type].json_encoder()
            json_str = json.dumps(d, cls=encoder)  # driver dependent JSON format
            serialized.append(json.loads(json_str))

        with open(file_path, "w") as f:
            json.dump(serialized, f, indent=4)

    def restore_configuration(self, file_path: str):
        """Load mutators from a file."""
        logging.info(f"Loading configuration from {file_path}.")
        with open(file_path, "r") as f:
            dictionary = json.load(f)
        for entry in dictionary:
            logging.debug(f"Entries: {entry}")
            if "sensor" not in entry:
                logging.error("Field 'sensor' must be present in the dictionary. Skipping.")
                continue
            if not isinstance(entry["sensor"], dict):
                logging.error("Field 'sensor' is not of dictionary type. Skipping.")
                continue
            if not "sensor_type" in entry.get("sensor"):
                logging.error("'sensor_type' cannot be determined. Skipping.")
                continue
            try:
                sensor_type = SensorType(entry.get("sensor").get("sensor_type"))
                factory: DriverFactory = self._sensor_factory_map[sensor_type]
            except KeyError:
                raise NotImplementedError(f"The case {entry['type']} is not implemented yet.")
            driver: DriverBase | SimulationDriver = factory.from_dict(entry)
            logging.info(f"Adding sensor {driver.sensor.name}.")
            self._sensors.append(driver.sensor)
            self._drivers.append(driver)

    def delete_sensor(self, sensor_id: SensorId):
        logging.info(f"Deleting sensor {sensor_id}.")
        mutator = next(x for x in self._drivers
                       if x.sensor.sensor_id == sensor_id)
        sensor = mutator.sensor
        sensor.stop()
        self._drivers.remove(mutator)
        self._sensors.remove(sensor)

    @property
    def state(self) -> State:
        """Get the current state of the machine."""
        return self._state

    @state.setter
    def state(self, value: State):
        """Set the current state of the machine."""
        logging.info(f"Setting state to {value}.")
        for m in self._drivers:
            m.state = value

        self._state = value

    @property
    def mode(self) -> Mode:
        """Get the current mode of the machine."""
        return self._mode

    @mode.setter
    def mode(self, value: Mode):
        """Set the current mode of the machine."""
        logging.info(f"Setting mode to {value}")
        for m in self._drivers:
            m.mode = value

        self._mode = value
