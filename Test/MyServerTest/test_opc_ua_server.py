import asyncio
from typing import Any

import pytest
from asyncua import Client, ua

from MyServer import OpcUaTestServer
from MyServer.Lifetime import MachineModelBase
from MyServer.MachineOperation import SensorId
from MyServer.Sensor import TemperatureSensor, SensorBase, Mutator


class MachineModelMock(MachineModelBase):
    def start_job(self):
        pass

    def stop_job(self):
        pass

    def custom_message(self, message: dict[str, Any]) -> bool:
        pass

    _sensors = []
    temperature = 0.0
    def restore_configuration(self, file_path: str):
        pass

    def save_configuration(self, file_path: str):
        pass

    @property
    def sensors(self) -> list[SensorBase]:
        return self._sensors

    def delete_sensor(self, sensor_id: SensorId):
        pass

    def get_temperature(self) -> float:
        return self.temperature

    def add_sensor(self, sensor: SensorBase, mutator: Mutator = None, **kwargs):
        if isinstance(sensor, TemperatureSensor):
            sensor.source = self.get_temperature
            assert sensor.source() == self.temperature

        self._sensors.append(sensor)


@pytest.fixture
def opc_ua_server():
    machine_mock = MachineModelMock()
    if len(machine_mock.sensors) == 0:  # just make sure some sensor is populated
        temperature_sensor = TemperatureSensor(1, updates_per_second=50)
        machine_mock.add_sensor(temperature_sensor)

    assert len(machine_mock.sensors) > 0, print("Sensor was not added to the system.")

    yield OpcUaTestServer(machine=machine_mock)

@pytest.mark.asyncio
async def test_setup_server(opc_ua_server: OpcUaTestServer):
    server_set_up: bool = await opc_ua_server.setup_server()
    assert server_set_up, "Server setup not completed."
    sensors: list[SensorBase] = opc_ua_server.model.sensors
    async with Client(url=opc_ua_server.end_point) as client:
        objects = client.nodes.objects
        children = await objects.get_children()
        browse_names = [await x.read_browse_name() for x in children]
        for sensor in sensors:
            if not sensor.running:
                sensor.start()
            folder_index: int = next((i for i, x in enumerate(browse_names) if x.Name == sensor.namespace), -1)
            assert folder_index >= 0, f"Unable to find namespace {sensor.namespace}."
            folder = children[folder_index]
            sensor_nodes = await folder.get_children()
            sensor_browse_names = [await x.read_browse_name() for x in sensor_nodes]
            sensor_index = next((i for i, x in enumerate(sensor_browse_names) if x.Name == sensor.name), -1)
            assert sensor_index >= 0, f"Unable to find sensor {sensor.name}."
            sensor_node = sensor_nodes[sensor_index]
            value_node = await sensor_node.get_child([f"{sensor_browse_names[sensor_index].NamespaceIndex}:Value"])
            time_node = await sensor_node.get_child([f"{sensor_browse_names[sensor_index].NamespaceIndex}:SensorTime"])
            assert value_node is not None
            assert time_node is not None
            value = await value_node.read_value()
            timestamp = await time_node.read_value()

            if isinstance(value, float):
                new_value = value + 1.0
                opc_ua_server.model.temperature = new_value
                await asyncio.sleep(2.0 / sensor.updates_per_second)
                test_value = await value_node.read_value()
                test_time = await time_node.read_value()
                assert abs(test_value - new_value) < 1e-12, f"Values mismatch: should be {new_value} but is {test_value}."
                assert test_time > timestamp, "Timestamp was not updated."
            else:
                raise NotImplementedError()
            sensor.stop()


