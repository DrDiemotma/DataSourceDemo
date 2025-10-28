from pydantic import BaseModel

from MyServer.MachineOperation import SensorType

SimulatorConfiguration = dict[str, int | float | bool | str |  dict[str, int | float | bool | str]]

class SensorConfig(BaseModel):
    """Configuration for a simulated sensor."""
    type: SensorType
    identifier: int
    simulator_config: SimulatorConfiguration | None
    model_config = {
        "frozen": True
    }

class SensorConfigList(BaseModel):
    """List sensor configs."""
    sensors: list[SensorConfig]
    model_config = {
        "frozen": True
    }

class SensorId(BaseModel):
    """A sensor ID."""
    type: SensorType
    """Type of the sensor."""
    identifier: int
    """Identifier number. Should be unique."""

    model_config = {
        "frozen": True
    }