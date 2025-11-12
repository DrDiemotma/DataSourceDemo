import os.path
import pytest
from datetime import datetime

from MyServer.MachineOperation import Mode, State, SensorType
from MyServer.Lifetime.machine_model import MachineModel
from MyServer.Sensor import TemperatureSensor, PressureSensor
from MyServer.Sensor.Base import SensorBase
from MyServer.Simulation import SimulationDriver



@pytest.fixture
def file_manager():
    file_dictionary: dict[str, str] = {
        x: os.path.join("./", x) for x in os.listdir("./") if x.endswith(".json")
    }
    yield file_dictionary
    for name, location in file_dictionary.items():
        print(f"Deleting {name}...")
        try:
            if os.path.isfile(location):
                os.remove(location)
                print(f"Deleted {name}.")
            else:
                print(f"File {name} already deleted.")
        except Exception as e:
            print(f"Could not delete {name} at {location}: {e}.")



class CustomSensor(SensorBase[int]):

    def _to_data_dictionary(self) -> dict:
        pass

    def on_polling(self):
        pass

    def to_data_object(self) -> dict:
        pass

class CustomMutator(SimulationDriver[int]):
    called = 0

    def _update_current_value(self) -> tuple[datetime, int]:
        self.called += 1
        return datetime.now(), self.called

    def to_driver_data(self) -> dict:
        pass


def test_add_custom_sensor():
    sut: MachineModel = MachineModel()
    sensor: CustomSensor = CustomSensor(name="Test", sensor_type=SensorType.TEMPERATURE, namespace="TestNamespace",
                                        updates_per_second=100, identifier=626)
    mutator: CustomMutator = CustomMutator(sensor, 0)
    sut.add_sensor(sensor, mutator)
    sut.mode = Mode.IDLE
    sut.state = State.NORMAL
    assert mutator.mode == Mode.IDLE, print("Mode not connected to mutator.")
    assert mutator.state == State.NORMAL, print("State not connected to mutator.")
    sut.mode = Mode.RUNNING
    sut.state = State.BROKEN
    assert mutator.mode == Mode.RUNNING, print("Mode not connected to mutator.")
    assert mutator.state == State.BROKEN, print("State not connected to mutator.")


def test_add_temperature_sensor():
    sensor: TemperatureSensor = TemperatureSensor(1)
    sut: MachineModel = MachineModel()
    old_mutator_count = len(sut.mutators)
    sut.add_sensor(sensor)
    assert len(sut.mutators) > old_mutator_count, "Mutator for temperature sensor was not created."

def test_add_pressure_sensor():
    sensor: PressureSensor = PressureSensor(1)
    sut: MachineModel = MachineModel()
    old_mutator_count = len(sut.mutators)
    sut.add_sensor(sensor)
    assert len(sut.mutators) > old_mutator_count, "Mutator for pressure sensor was not created."

def test_save_configuration(file_manager):

    test_file_name: str = "test_machine_model_configuration.json"
    file_manager[test_file_name] = os.path.abspath(test_file_name)
    if os.path.isfile(file_manager[test_file_name]):
        try:
            os.remove(file_manager[test_file_name])
        except Exception as e:
            print("Was not able to delete the test file.")
            raise e

    sensor: TemperatureSensor = TemperatureSensor(1)
    sensor2: TemperatureSensor = TemperatureSensor(2)
    sut: MachineModel = MachineModel()
    sut.add_sensor(sensor)
    sut.add_sensor(sensor2)
    sut.save_configuration(file_manager[test_file_name])
    assert os.path.isfile(file_manager[test_file_name]), print("Testfile was not written")
    os.remove(file_manager[test_file_name])

def test_restore_configuration(file_manager):
    test_file_name: str = "test_machine_model_configuration.json"
    file_manager[test_file_name] = os.path.abspath(test_file_name)
    if os.path.isfile(file_manager[test_file_name]):
        try:
            os.remove(file_manager[test_file_name])
        except Exception as e:
            print("Was not able to delete the test file.")
            raise e

    sensor: TemperatureSensor = TemperatureSensor(1)
    sensor2: TemperatureSensor = TemperatureSensor(2)
    creator: MachineModel = MachineModel()
    creator.add_sensor(sensor)
    creator.add_sensor(sensor2)
    creator.save_configuration(file_manager[test_file_name])
    assert os.path.isfile(file_manager[test_file_name]), print("Testfile was not written")

    sut: MachineModel = MachineModel()
    sut.restore_configuration(file_manager[test_file_name])
    mutators = sut.mutators
    assert len(mutators) == 2, print(f"Two mutators assumed, got {len(mutators)}.")
    sensor_names = [mutator.sensor.name for mutator in mutators]
    assert sensor.name in sensor_names, print(f"Sensor {sensor.name} not in loaded sensors.")
    assert sensor2.name in sensor_names, print(f"Sensor {sensor2.name} not in sensors.")
    os.remove(file_manager[test_file_name])