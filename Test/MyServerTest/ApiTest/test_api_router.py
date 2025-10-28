from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient

from MyServer.Lifetime import MachineModel
from MyServer.MachineOperation.sensor_data_model import SensorId
from main import app, opc_ua_server

from MyServer.Api import SensorConfig
from MyServer.MachineOperation import SensorType

@pytest.fixture
def client() -> Generator[TestClient, Any, None]:
    # rewrite the state
    server = opc_ua_server.OpcUaTestServer(machine=MachineModel())
    app.state.server = server
    with TestClient(app) as client:
        yield client


def test_add_sensor_simulator_config_none(client: TestClient):
    sensor_config: SensorConfig = SensorConfig(type=SensorType.TEMPERATURE, identifier=42, simulator_config=None)
    # client: TestClient = create_test_client()
    response = client.post("/add_sensor", json=sensor_config.model_dump())
    assert response.is_success, print(response)

def test_get_sensors(client: TestClient):
    sensor_config: SensorConfig = SensorConfig(type=SensorType.TEMPERATURE, identifier=42, simulator_config=None)
    response = client.post("/add_sensor", json=sensor_config.model_dump())
    assert response.is_success, print(response)

    response = client.get("/get_sensors")
    assert response.is_success
    data = response.json()
    assert "sensors" in data, print(f"Response model must include \"sensors\".")
    assert len(data["sensors"]) > 0, print("Sensors must not be empty.")

def test_delete_sensor(client: TestClient):
    sensor_config: SensorConfig = SensorConfig(type=SensorType.TEMPERATURE, identifier=97, simulator_config=None)
    response = client.post("/add_sensor", json=sensor_config.model_dump())
    assert response.is_success, print(response)

    sensor_id = SensorId(
        identifier=sensor_config.identifier,
        type=sensor_config.type
    )

    response = client.post("/delete_sensor", json=sensor_id.model_dump())
    assert response.is_success, print(response)

    response = client.get("/get_sensors")
    assert response.is_success, print(response)
    assert len(response.json()["sensors"]) == 0, print("Sensor was not deleted.")


