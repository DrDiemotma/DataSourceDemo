import asyncio
import pytest
from datetime import datetime

from pandas.core.methods.describe import describe_timestamp_1d

from MyServer.Sensor.Modification.TemperatureMutator import TemperatureMutator, TemperatureMutatorFactory
from MyServer.Sensor import TemperatureSensor
from MyServer.MachineOperation import State, Mode

class TestSensorConsumer:
    temperature: float
    time_stamp: datetime
    def callback(self, time_stamp: datetime, value: float):
        self.time_stamp = time_stamp
        self.temperature = value


def test_measure():
    sensor: TemperatureSensor = TemperatureSensor(1)
    sut: TemperatureMutator = TemperatureMutator(sensor, start_value=20.0)
    value: float = sut.measure()
    assert 15.0 < value < 25.0  # should be around 20 degrees plus some noise.

@pytest.mark.asyncio
async def test_updates():
    sensor: TemperatureSensor = TemperatureSensor(1, updates_per_second=100)
    consumer = TestSensorConsumer()
    sensor.add_callback(consumer.callback)
    sut: TemperatureMutator = TemperatureMutator(sensor, start_value=20.0, value_running=200)
    sensor.start()
    await asyncio.sleep(2.0 / sensor.updates_per_second)  # make sure data is written
    start_temperature = consumer.temperature
    start_time = consumer.time_stamp
    assert start_temperature > 0
    assert start_time is not None
    sut.mode = Mode.RUNNING
    await asyncio.sleep(10.0 / sensor.updates_per_second)  # make sure value has time to increase
    sensor.stop()
    end_temperature = consumer.temperature
    end_time = consumer.time_stamp

    assert end_temperature > start_temperature
    assert end_time > start_time

@pytest.mark.asyncio
async def test_adaption():
    sensor: TemperatureSensor = TemperatureSensor(1, updates_per_second=100)
    consumer = TestSensorConsumer()
    sensor.add_callback(consumer.callback)
    # don't increase the st_dev value, this is here to have a very deterministic behaviour of temperature
    sut: TemperatureMutator = TemperatureMutator(sensor, start_value=20.0, value_running=200, st_dev=10e-8)
    sensor.start()
    await asyncio.sleep(2.0 / sensor.updates_per_second) # make sure data is written
    raw_data = [consumer.temperature] * 10
    sut.mode = Mode.RUNNING
    for i in range(1, 10):
        await asyncio.sleep(1.0 / sensor.updates_per_second)
        raw_data[i] = consumer.temperature
    sensor.stop()  # we don't need to have it running for the rest of the test, just see that the data increases
    last_difference = 10000.0
    for i in range(1, 10):
        ascend = raw_data[i] - raw_data[i - 1]
        assert ascend > 0, print("")  # should always increase
        assert ascend < last_difference, print("Temperature was expected to rise asymptotically, but went from"
                                              f"{last_difference} to {ascend}.")  # slows down ofer time
        last_difference = ascend

def test_to_dict():
    sensor: TemperatureSensor = TemperatureSensor(1)
    sensor_dict: dict = sensor.to_dict()
    d = {
        "sensor": sensor,
        "start_value": 21.7,
        "random_seed": 123,
        "st_dev": 1.2,
        "value_idle": 18.6,
        "value_running": 72.8,
        "value_running_broken": 161.91,
        "adaption_rate": 0.262
    }
    sut: TemperatureMutator = TemperatureMutator(**d)
    description = sut.to_dict()

    for key, value in d.items():
        assert key in description
        v_test = description[key]
        if isinstance(value, (int, float)):
            assert abs(value - v_test) < 10e-12, print(f"Values for \"{key}\" to dissimilar: expected {value}, got {v_test}.")
        elif isinstance(value, str):
            assert value == v_test, print(f"Field {key} was not equal: expected \"{value}\", got \"{v_test}\"")
        elif isinstance(value, TemperatureSensor):
            target_dict = value.to_dict()
            for sensor_key, sensor_value in sensor_dict.items():
                assert sensor_key in target_dict, print(f"Key {sensor_key} expected but not in result dict.")
                target_dict_value = target_dict[sensor_key]
                if isinstance(sensor_value, (int, float)):
                    assert abs(sensor_value - target_dict_value) < 10e-12, print(f"Values for {key}.{sensor_key} too" 
                        f"dissimilar, expected {sensor_value}, got {target_dict_value}")
                elif isinstance(sensor_value, str):
                    assert sensor_value == target_dict_value, print(f"Field {key}.{sensor_key} not equal: expected"
                        f"{sensor_value}, got {target_dict_value}")
                else:
                    raise NotImplementedError(f"The field {key}.{sensor_key} is not tested for.")
        else:
            raise NotImplementedError(f"The field {key} is not tested for.")

def test_temperature_mutator_factory():
    sensor: TemperatureSensor = TemperatureSensor(1)
    sensor_dict: dict = sensor.to_dict()
    d = {
        "sensor": sensor,
        "start_value": 21.7,
        "random_seed": 123,
        "st_dev": 1.2,
        "value_idle": 18.6,
        "value_running": 72.8,
        "value_running_broken": 161.91,
        "adaption_rate": 0.262
    }
    mutator: TemperatureMutator = TemperatureMutatorFactory.from_dict(d)
    description = mutator.to_dict()

    for key, value in d.items():
        assert key in description
        v_test = description[key]
        if isinstance(value, (int, float)):
            assert abs(value - v_test) < 10e-12, print(f"Values for \"{key}\" to dissimilar: expected {value}, got {v_test}.")
        elif isinstance(value, str):
            assert value == v_test, print(f"Field {key} was not equal: expected \"{value}\", got \"{v_test}\"")
        elif isinstance(value, TemperatureSensor):
            target_dict = value.to_dict()
            for sensor_key, sensor_value in sensor_dict.items():
                assert sensor_key in target_dict, print(f"Key {sensor_key} expected but not in result dict.")
                target_dict_value = target_dict[sensor_key]
                if isinstance(sensor_value, (int, float)):
                    assert abs(sensor_value - target_dict_value) < 10e-12, print(f"Values for {key}.{sensor_key} too" 
                        f"dissimilar, expected {sensor_value}, got {target_dict_value}")
                elif isinstance(sensor_value, str):
                    assert sensor_value == target_dict_value, print(f"Field {key}.{sensor_key} not equal: expected"
                        f"{sensor_value}, got {target_dict_value}")
                else:
                    raise NotImplementedError(f"The field {key}.{sensor_key} is not tested for.")
        else:
            raise NotImplementedError(f"The field {key} is not tested for.")

