import pytest

from MyServer.Simulation import TemperatureSimulationDriver, TemperatureSimulationDriverFactory
from MyServer.Sensor import TemperatureSensor



@pytest.fixture
def temperature_sensor():
    yield TemperatureSensor(1)

def test_to_dict(temperature_sensor):
    sut = TemperatureSimulationDriver(temperature_sensor)
    description = sut.to_driver_data()
    assert description is not None, "No return value."
    json_format = description.as_dict()
    assert json_format is not None, "No JSON generation."
    assert "sensor" in json_format

def test_from_dict(temperature_sensor):
    driver = TemperatureSimulationDriver(temperature_sensor)
    description = driver.to_driver_data().as_dict()  # this is the format to be read from a file
    new_driver = TemperatureSimulationDriverFactory.from_dict(description)
    new_description = new_driver.to_driver_data().as_dict()
    for key, value in description.items():
        assert key in new_description, f"Key {key} not in new description."
        if isinstance(value, str):
            assert value == new_description[key], f"Key {key}: expected {value}, got {new_description[key]}."
        if isinstance(value, int):
            assert value == new_description[key], f"Key {key}: expected {value}, got {new_description[key]}."
        if isinstance(value, float):
            assert abs(value - new_description[key]) < 1e-8, f"Key {key}: expected {value}, got {new_description[key]}."

    for key in new_description.keys():
        assert key in description, f"Key {key} not in old description."