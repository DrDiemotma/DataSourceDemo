from fastapi import APIRouter, Request
import logging
from MyServer import OpcUaTestServer
from MyServer.Lifetime import MachineModelBase
from MyServer.MachineOperation import SensorConfig, SensorConfigList, SensorId
from MyServer.MachineOperation import SensorType
from MyServer.Sensor import TemperatureSensor
from MyServer.Sensor.Base import SensorBase, SensorDictBase
from MyServer.Simulation import TemperatureSimulationDriver


router_v01 = APIRouter()

@router_v01.get("/status",
                summary="Get the status",
                description="Get the current status of the server.")
async def status(request: Request):
    server: OpcUaTestServer = request.app.state.server

    return {
        "status": "ok" if server is not None else "nok",
        "version": "0.1"
    }

@router_v01.post("/start",
                 summary="Start the server")
async def start(request: Request):
    logging.info("Starting the machine.")
    server: OpcUaTestServer = request.app.state.server
    await server.start()

@router_v01.post("/stop")
async def stop(request: Request):
    logging.info("Stopping the machine.")
    server: OpcUaTestServer = request.app.state.server
    await server.stop()

@router_v01.get("/is_running")
async def is_running(request: Request):
    server: OpcUaTestServer = request.app.state.server
    result = server.alive_status()
    logging.info(f"Requested running status. Result: {result}.")
    return result

@router_v01.post("/add_sensor")
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
