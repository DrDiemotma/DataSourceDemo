from fastapi import APIRouter

from MyServer.MachineOperation import SensorType, SensorConfig

router_examples = APIRouter()

@router_examples.get("/example_config/{sensor_type}", response_model=SensorConfig)
async def example_config(sensor_type: SensorType):
    sensor_config: SensorConfig | None = None
    match sensor_type:
        case SensorType.TEMPERATURE:
            simulator_config = {
                "start_value": 23.0,
                "value_idle": 23.0,
                "value_running": 85.0,
                "value_running_broken": 105.5,
                "random_seed": 42,
                "adaption_rate": 0.2,
                "st_dev": 0.5
            }
            sensor_config = SensorConfig(type=SensorType.TEMPERATURE, identifier=1234, simulator_config=simulator_config)
        case SensorType.PRESSURE:
            simulator_config = {
                "start_value": 1013.0,
                "random_seed": 42,
                "st_dev": 4.5,
                "st_dev_broken": 8.5,
                "value_idle": 1013.0,
                "value_running": 1220.0,
                "value_running_broken": 1120.0,
                "adaption_rate": 0.5
            }
            sensor_config = SensorConfig(type=SensorType.PRESSURE, identifier=1234, simulator_config=simulator_config)


    return sensor_config