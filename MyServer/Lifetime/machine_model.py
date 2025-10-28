import json
from typing import Any
import logging

from MyServer.Lifetime.machine_model_base import MachineModelBase
from MyServer.MachineOperation.sensor_data_model import SensorId
from MyServer.MachineOperation import State, Mode, SensorType
from MyServer.Sensor import SensorBase, Mutator, TemperatureSensor
from MyServer.Sensor.Modification.TemperatureMutator import TemperatureMutator, TemperatureMutatorFactory
from MyServer.Sensor.Modification.mutator import MutatorFactory

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
        for mutator in self._mutators:
            mutator.mode = Mode.RUNNING

    def stop_job(self):
        logging.info("Stopping job.")
        for mutator in self._mutators:
            mutator.mode = Mode.IDLE

    def set_state_broken(self):
        logging.info("Setting machine state to \"broken\".")
        for mutator in self._mutators:
            mutator.state = State.BROKEN

    def set_state_normal(self):
        logging.info("Setting machine state to \"normal\".")
        for mutator in self._mutators:
            mutator.state = State.NORMAL

    def __init__(self):
        self._sensors: list[SensorBase] = []
        self._mutators: list[Mutator] = []
        self._state: State = State.NORMAL
        self._mode: Mode = Mode.RUNNING

        self._sensor_factory_map: dict[SensorType, MutatorFactory] = {
            SensorType.TEMPERATURE: TemperatureMutatorFactory(),
        }

    def __del__(self):
        for sensor in self._sensors:
            sensor.stop()

    def add_sensor(self, sensor: SensorBase, mutator: Mutator = None, **kwargs):
        """
        Add a sensor.
        :param sensor: Sensor to add.
        :param mutator: mutator for the sensor. If None, a default mutator is created for the respective sensor.
        """
        logging.info(f"Adding sensor {sensor.name}, type {sensor.sensor_type}, to machine.")
        self._sensors.append(sensor)
        if mutator is not None:
            logging.info(f"Mutator for sensor {sensor.name} given, continue with present one.")
            mutator.state = self._state
            mutator.mode = self._mode
            self._mutators.append(mutator)
            return

        logging.info(f"No mutator for sensor {sensor.name} given, use default configuration.")
        # create the mutator automatically
        if isinstance(sensor, TemperatureSensor):
            logging.info(f"Adding {sensor.name} as temperature sensor.")
            temperature_mutator: TemperatureMutator =  TemperatureMutator(sensor, **kwargs)
            temperature_mutator.state = self._state
            temperature_mutator.mode = self._mode
            self._mutators.append(temperature_mutator)

    @property
    def mutators(self) -> list[Mutator]:
        """Get a list of current mutators to fine-tune behaviour."""
        return list(self._mutators)

    @property
    def sensors(self) -> list[SensorBase]:
        """Get the sensors"""
        return [x.sensor for x in self._mutators]


    def save_configuration(self, file_path: str):
        """Save the current configuration to a file."""
        logging.info(f"Saving configuration to file {file_path}.")
        data = [sensor.to_dict() for sensor in self._sensors]
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

    def restore_configuration(self, file_path: str):
        """Load mutators from a file."""
        logging.info(f"Loading configuration from {file_path}.")
        with open(file_path, "r") as f:
            dictionary = json.load(f)
        for entry in dictionary:
            logging.debug(f"Entries: {entry}")
            sensor_type = SensorType(entry["type"])
            try:
                factory: MutatorFactory = self._sensor_factory_map[sensor_type]
            except KeyError:
                raise NotImplementedError(f"The case {entry['type']} is not implemented yet.")
            mutator: Mutator = factory.from_dict(entry)
            logging.info(f"Adding sensor {mutator.sensor.name}.")
            self._sensors.append(mutator.sensor)
            self._mutators.append(mutator)

    def delete_sensor(self, sensor_id: SensorId):
        logging.info(f"Deleting sensor {sensor_id}.")
        mutator = next(x for x in self._mutators
                       if x.sensor.sensor_id == sensor_id)
        sensor = mutator.sensor
        sensor.stop()
        self._mutators.remove(mutator)
        self._sensors.remove(sensor)

    @property
    def state(self) -> State:
        """Get the current state of the machine."""
        return self._state

    @state.setter
    def state(self, value: State):
        """Set the current state of the machine."""
        logging.info(f"Setting state to {value}.")
        for m in self._mutators:
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
        for m in self._mutators:
            m.mode = value

        self._mode = value
