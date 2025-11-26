from fastapi import APIRouter, Request
import logging
from MyServer import OpcUaTestServer
from MyServer.Lifetime import MachineModelBase
from MyServer.MachineOperation import SensorConfig, SensorConfigList, SensorId
from MyServer.MachineOperation import SensorType
from MyServer.Sensor import TemperatureSensor
from MyServer.Sensor.Base import SensorBase, SensorDictBase
from MyServer.Simulation import TemperatureSimulationDriver
from .examples import router_examples


router_v01 = APIRouter()

@router_v01.get("/status",
                summary="Get the status.",
                description="Get the current status of the server.")
async def status(request: Request):
    server: OpcUaTestServer = request.app.state.server

    return {
        "status": "ok" if server is not None else "nok",
        "version": "0.1"
    }

@router_v01.post("/start",
                 summary="Start the server.",
                 description="Start the server with all installed sensors. No sensor can be added in this phase.")
async def start(request: Request):
    logging.info("Starting the machine.")
    server: OpcUaTestServer = request.app.state.server
    await server.start()

@router_v01.post("/stop",
                 summary="Stop the server.",
                 description="Stop the running server. New sensors can be added in this phase.")
async def stop(request: Request):
    logging.info("Stopping the machine.")
    server: OpcUaTestServer = request.app.state.server
    await server.stop()

@router_v01.get("/is_initialized",
                summary="Returns whether the system is initialized.",
                description="The initialization is simulating the boot up of the machine. If the machine is not set "
                    "up, it cannot be started. Internally, this starts the OPC UA server.")
async def is_initialized(request: Request):
    server: OpcUaTestServer = request.app.state.server
    result = server.is_initialized
    logging.info(f"Requested is initialized, result: {result}")
    return result

@router_v01.get("/is_running",
                summary="Get whether the server is currently running.",
                description="Requests from the server whether the machine is running.")
async def is_running(request: Request):
    server: OpcUaTestServer = request.app.state.server
    result = server.alive_status()
    logging.info(f"Requested running status. Result: {result}.")
    return result

@router_v01.post("/add_sensor",
                 summary="Add a sensor to the server.",
                 description="Add a sensor. Does work only if the server is not running.")
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
                    temperature_mutator: TemperatureSimulationDriver = TemperatureSimulationDriver(
                        temperature_sensor,
                        **sensor_config.simulator_config
                    )
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

@router_v01.post("/delete_sensor",
                 summary="Delete a sensor.",
                 description="Delete a sensor given by its SensorId")
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

@router_v01.get("/get_sensors", response_model=SensorConfigList,
                summary="Get a list of the installed sensors.",
                description="Get the installed sensors as a list.")
async def get_sensors(request: Request):
    logging.info("List of sensors requested.")
    def to_sensor_config(s: SensorBase) -> SensorConfig:
        dictionary: SensorDictBase = s.to_data_object()
        config: SensorConfig = SensorConfig(
            type=dictionary.sensor_type,
            identifier=s.identifier,
            simulator_config=None
        )
        return config

    server: OpcUaTestServer = request.app.state.server
    sensors: list[SensorBase] = server.model.sensors
    logging.debug(f"Number of sensors: {len(sensors)}.")
    config_list = SensorConfigList(sensors=[to_sensor_config(x) for x in sensors])
    return config_list

@router_v01.post("/initialize",
                 summary="Initialize the machine.",
                 description="Start the machine. This simulates the boot up of the machine itself. Practically, this "
                    "initializes the OPC UA server.")
async def initialize(request: Request):
    server: OpcUaTestServer = request.app.state.server
    already_initialized = server.is_initialized
    if already_initialized:
        logging.info("Request for initialization, but already initialized. Skipping.")
        return False
    result = await server.setup_server()
    if result:
        logging.info("Setting up server successful.")
    else:
        logging.error("Setting up server failed.")
    return result


@router_v01.post("/start_job",
                 summary="Start a job.",
                 description="Start a job. In Detail, this switches all simulated sensors in \"working\" mode.")
async def start_job(request: Request):
    logging.info("Start of job requested.")
    server: OpcUaTestServer = request.app.state.server
    started = await server.start_job()
    logging.info(f"Start of job, is started: {started}.")
    return started

@router_v01.post("/stop_job",
                 summary="Stop the running job.",
                 description="Stop the running job. Does nothing if the job is not running.")
async def stop_job(request: Request):
    logging.info("Stop of job requested.")
    server: OpcUaTestServer = request.app.state.server
    stopped = await server.stop_job()
    logging.info(f"Sop of job, stopped: {stopped}.")
    return stopped

@router_v01.post("/is_job_running")
async def is_job_running(request: Request):
    server: OpcUaTestServer = request.app.state.server
    job_running: bool = server.is_job_running
    logging.info(f"Request whether job is running: {job_running}.")
    return job_running

@router_v01.post("/custom_message",
                 summary="Send a custom message to the server.",
                 description="Send a custom message. Used for higher level and debug controls.")
async def custom_message(message, request: Request):
    logging.info("Received custom message.")
    logging.debug(f"Message: {message}")
    server: OpcUaTestServer = request.app.state.server
    model: MachineModelBase = server.model
    success = model.custom_message(message)
    logging.info(f"Custom message success: {success}.")
    return success

