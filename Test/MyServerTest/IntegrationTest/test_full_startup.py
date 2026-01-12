from typing import Generator, Any

from fastapi.testclient import TestClient

from MyServer.Lifetime import MachineModel
from main import app, opc_ua_server

import pytest

@pytest.fixture
def client() -> Generator[TestClient, Any, None]:
    server = opc_ua_server.OpcUaTestServer(machine=MachineModel())
    app.state.server = server
    with TestClient(app) as client:
        yield client


def test_startup(client: TestClient):
    raise NotImplementedError()