import asyncio
import pytest


from MyServer.Sensor import TemperatureSensor
from datetime import datetime

class TestTemperatureSource:
    read: bool = False
    callback_called: bool = False
    callback_called_when: datetime
    callback_called_value: float
    last_value = 0.0

    def read_value(self) -> float:
        self.read = True
        self.last_value += 1.0
        return self.last_value

    def callback(self, dt: datetime, f: float):
        self.callback_called = True
        self.callback_called_when = dt
        self.callback_called_value = f


def test_namespace_namespace_set():
    sut: TemperatureSensor = TemperatureSensor(1)
    assert len(sut.namespace) > 0

def test_temperature_name_set():
    sut: TemperatureSensor = TemperatureSensor(1)
    assert len(sut.name) > 0

def test_updates_per_seconds_set():
    sut: TemperatureSensor = TemperatureSensor(1)
    assert sut.updates_per_second > 0

@pytest.mark.asyncio
async def test_start_top():  # async to make sure that an event loop is running
    test_sensor: TestTemperatureSource = TestTemperatureSource()
    sut: TemperatureSensor = TemperatureSensor(1)
    assert sut.running == False
    # test that start is blocked as long as no source is given
    sut.start()
    assert sut.running == False
    sut.source = test_sensor.read_value
    sut.start()
    assert sut.running == True
    sut.stop()
    assert sut.running == False

@pytest.mark.asyncio
async def test_set_source():
    test_sensor: TestTemperatureSource = TestTemperatureSource()
    sut: TemperatureSensor = TemperatureSensor(1)
    assert not sut.running
    assert sut.source is None
    sut.source = test_sensor.read_value
    sut.start()
    await asyncio.sleep(2.0/sut.updates_per_second)  # let the value update
    sut.stop()
    assert test_sensor.read == True

@pytest.mark.asyncio
async def test_callback():
    test_sensor: TestTemperatureSource = TestTemperatureSource()
    sut: TemperatureSensor = TemperatureSensor(1)
    sut.source = test_sensor.read_value
    sut.add_callback(test_sensor.callback)
    sut.start()
    await asyncio.sleep(2.0 / sut.updates_per_second)
    sut.stop()
    assert test_sensor.callback_called
    assert test_sensor.callback_called_value > 0


def test_to_dict():
    d = {
        "identifier": 42,
        "namespace": "Sensors",
        "updates_per_second": 0.123
    }
    sensor: TemperatureSensor = TemperatureSensor(**d)
    d2 = sensor.to_dict()

    for key in d.keys():
        assert key in d2
        assert d[key] == d2[key]
