from fastapi import APIRouter

from MyServer.MachineOperation import SensorType
from MyServer.Sensor import TemperatureSensor, PressureSensor
from MyServer.Simulation import TemperatureSimulationDriver, SimulationDriver, PressureSimulationDriver

router_examples = APIRouter()

@router_examples.get("/example_config/{sensor_type}")
async def example_config(sensor_type: SensorType):
    simulation_driver: SimulationDriver | None = None
    match sensor_type:
        case SensorType.TEMPERATURE:
            temperature_sensor = TemperatureSensor(1234)
            simulation_driver = TemperatureSimulationDriver(temperature_sensor)
        case SensorType.PRESSURE:
            pressure_sensor = PressureSensor(1234)
            simulation_driver = PressureSimulationDriver(pressure_sensor)

    if simulation_driver is not None:
        return simulation_driver.to_driver_data().as_dict()

    return None