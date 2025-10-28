from fastapi import APIRouter, Request
import logging

from MyServer import OpcUaTestServer
from MyServer.Lifetime import MachineModelBase
from MyServer.MachineOperation import SensorConfig, SensorConfigList, SensorId
from MyServer.MachineOperation import SensorType
from MyServer.Sensor import TemperatureSensor, SensorBase
from MyServer.Sensor.Modification.TemperatureMutator import TemperatureMutator

router: APIRouter = APIRouter()

@router.post("/add_sensor")
async def add_sensor(sensor_config: SensorConfig, request: Request):
    logging.info(f"Adding sensor: {sensor_config.type}: {sensor_config.identifier}")
    if sensor_config.simulator_config is not None:
        logging.info("Simulator config found.")
    server: OpcUaTestServer = request.app.state.server
    match sensor_config.type:
        case SensorType.TEMPERATURE:
            temperature_sensor: TemperatureSensor = TemperatureSensor(sensor_config.identifier)
            if not sensor_config.simulator_config is None:
                try:
                    temperature_mutator: TemperatureMutator = TemperatureMutator(temperature_sensor, **sensor_config.simulator_config)
                    logging.debug(f"Adding sensor {temperature_sensor.name} with mutator.")
                    server.model.add_sensor(temperature_sensor, temperature_mutator)
                except Exception as e:
                    logging.error(f"Error caught: {e} config: {sensor_config.simulator_config}. Using default config.")
                    server.model.add_sensor(temperature_sensor)
            else:
                logging.debug("Using default configuration.")
                server.model.add_sensor(temperature_sensor)
            return True

    return False


@router.get("/get_sensors", response_model=SensorConfigList)
async def get_sensors(request: Request):
    logging.info("List of sensors requested.")
    def to_sensor_config(s: SensorBase) -> SensorConfig:
        dictionary = s.to_dict()
        config: SensorConfig = SensorConfig(
            type=dictionary["type"],
            identifier=s.identifier,
            simulator_config=None
        )
        return config

    server: OpcUaTestServer = request.app.state.server
    sensors: list[SensorBase] = server.model.sensors
    logging.debug(f"Number of sensors: {len(sensors)}.")
    config_list = SensorConfigList(sensors=[to_sensor_config(x) for x in sensors])
    return config_list

@router.post("/delete_sensor")
async def delete_sensor(sensor_id: SensorId, request: Request):
    logging.info(f"Deletion of sensor {sensor_id} requested.")
    server: OpcUaTestServer = request.app.state.server
    sensor = next((x for x in server.model.sensors if x.sensor_type == sensor_id.type and x.identifier == sensor_id.identifier), None)
    if sensor is None:
        logging.warning(f"Sensor {sensor_id} not found.")
        return False

    server.model.delete_sensor(sensor_id)
    logging.info(f"Sensor {sensor_id} deleted.")
    return True

@router.post("/start")
async def start(request: Request):
    logging.info("Starting the machine.")
    server: OpcUaTestServer = request.app.state.server
    await server.start()

@router.post("/stop")
async def stop(request: Request):
    logging.info("Stopping the machine.")
    server: OpcUaTestServer = request.app.state.server
    await server.stop()

@router.get("/is_running")
async def is_running(request: Request):
    server: OpcUaTestServer = request.app.state.server
    result = server.alive_status()
    logging.info(f"Requested running status. Result: {result}.")
    return result

@router.post("/start_job")
async def start_job(request: Request):
    logging.info("Start of job requested.")
    server: OpcUaTestServer = request.app.state.server
    started = await server.start_job()
    logging.info(f"Start of job, is started: {started}.")
    return started

@router.post("/stop_job")
async def stop_job(request: Request):
    logging.info("Stop of job requested.")
    server: OpcUaTestServer = request.app.state.server
    stopped = await server.stop_job()
    logging.info(f"Sop of job, stopped: {stopped}.")
    return stopped

@router.post("/custom_message")
async def custom_message(message, request: Request):
    logging.info("Received custom message.")
    logging.debug(f"Message: {message}")
    server: OpcUaTestServer = request.app.state.server
    model: MachineModelBase = server.model
    success = model.custom_message(message)
    logging.info(f"Custom message success: {success}.")
    return success
