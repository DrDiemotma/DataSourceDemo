import json

import asyncua
import asyncio
import os
from asyncua import ua
from asyncua.ua import VariantType
import logging

from MyServer.Lifetime.machine_model_base import MachineModelBase
from MyServer.OpcUa import ServerConfiguration, variant_type
from datetime import datetime


OPC_TCP: str = "opc.tcp"
IP_ADDRESS: str = "0.0.0.0"
OPC_UA_PORT: int = 4840
COMPANY: str = "TestCompany.com"
SERVER_ENDPOINT: str = "freeopcua/server"
URI: str = "http://example.org/opcua"
DEVICE: str = "Device"
SENSOR_URI: str = "sensors"
TEMPERATURE: str = "Temperature"
PRESSURE: str = "Pressure"
FREQ: float = 1.0
TEMPERATURE_START_VALUE: float = 20.0
PRESSURE_START_VALUE: float = 1013.25
CONFIGURATION_FILE: str = "MachineModel.json"

class OpcUaTestServer:
    """
    Test OPC UA server with some simulated values as output.
    """

    def __init__(self,
                 machine: MachineModelBase,
                 freq: float = FREQ,
                 server_endpoint: str = SERVER_ENDPOINT,
                 server_configuration: ServerConfiguration | None = None,
                 machine_model_file: str = CONFIGURATION_FILE,
                 sensor_uri: str = SENSOR_URI):
        """
        ctor.
        :param freq: Frequency control, distance between two samples. Used for clean shutdowns.
        :param server_endpoint: Definition for the server endpoint.
        :param server_configuration: Configuration for the server.
        :param machine_model_file: File to store the configuration of the machine model.
        :param sensor_uri: URI for the sensor.
        :param machine: Machine representation.
        """
        logging.info(f"Creating OpcUaTestServer with {freq=} {server_endpoint=} {server_configuration=} {machine_model_file=} {sensor_uri=}")
        self._freq = freq
        self._stopped = True
        if server_configuration is None:
            server_configuration = ServerConfiguration(
                company=COMPANY,
                ip_address=IP_ADDRESS,
                device_name=DEVICE,
                port=OPC_UA_PORT,
                fields=[sensor_uri]
            )
        if sensor_uri not in server_configuration.fields:
            server_configuration.fields.append(sensor_uri)
        self._configuration: ServerConfiguration = server_configuration
        self._machine_model_file = machine_model_file
        self._set_up: bool = False

        self._end_point: str = (OPC_TCP
                                + "://" + IP_ADDRESS
                                + ":" + str(self._configuration.port)
                                + "/" + server_endpoint + "/")

        self._server: asyncua.Server = asyncua.Server()
        self._model: MachineModelBase = machine
        if os.path.isfile(machine_model_file):
            self._model.restore_configuration(self._machine_model_file)

    @property
    def model(self) -> MachineModelBase:
        return self._model

    @property
    def configuration(self):
        """Get the current configuration."""
        return self._configuration

    @property
    def end_point(self):
        """Get the end point of the server."""
        return self._end_point

    def alive_status(self) -> bool:
        """Return whether the server is set up."""
        return self._set_up and not self._stopped  # this is too simplified, lets rework this later

    async def setup_server(self) -> bool:
        """
        Set up the server.
        :returns: Whether setup was successful.
        """
        if self._set_up or not self._stopped:
            logging.warning(f"Tried to setup the server, but set up = {self._set_up}, stopped = {self._stopped}.")
            return False

        await self._server.init()
        self._server.set_endpoint(self._end_point)
        self._server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
        sensor_uri: str = self.get_uri(self._configuration.sensors)
        sensor_idx: int = await self._server.register_namespace(sensor_uri)
        objects: asyncua.Node = self._server.nodes.objects
        sensor_folder: asyncua.Node = await objects.add_folder(sensor_idx, self._configuration.sensors)
        for sensor in self._model.sensors:
            logging.info(f"Trying to add {sensor.name} to the data model.")
            if sensor.namespace != self._configuration.sensors:
                logging.warning(f"Alternative sensor folder not implemented yet, skipping {sensor.name}.")
            registered_sensor: asyncua.Node = await sensor_folder.add_object(sensor_idx, sensor.name)
            variant, default_value = variant_type(sensor.sensor_type)
            value_field: asyncua.Node = await registered_sensor.add_variable(sensor_idx,
                                                                             "Value",
                                                                             default_value,
                                                                             varianttype=variant)
            time_field: asyncua.Node = await registered_sensor.add_variable(sensor_idx,
                                                                            "SensorTime",
                                                                            datetime.now(),
                                                                            varianttype=VariantType.DateTime)
            await value_field.set_writable()

            sensor.add_callback(self._make_callback(value_field, time_field, variant))
            if not sensor.running:
                sensor.start()
            logging.info(f"Sensor {sensor.name} added.")
        logging.info("All sensors added, starting OPC UA server.")
        await self._server.start()
        await asyncio.sleep(0.05)  # asyncua is not reliable, hence better wait for a bit here
        logging.info("Everything set up.")
        self._set_up = True
        return True

    @staticmethod
    def _make_callback(value_field: asyncua.Node, datetime_field: asyncua.Node, vt: ua.VariantType):
        async def callback(ts: datetime, v):
            variant = ua.Variant(v, vt)
            await value_field.set_value(variant)
            await datetime_field.set_value(ua.Variant(ts, VariantType.DateTime))

        return callback

    async def start(self):
        if self._server is None:
            logging.info("Starting server")
            await self.setup_server()
            return True
        logging.warning("Server already running")
        return False

    async def stop(self):
        logging.info("Stopping server")
        for sensor in self._model.sensors:
            sensor.stop()
        await self._server.stop()
        self._stopped = True
        await asyncio.sleep(0.01 + self._freq)
        logging.info("Server stopped.")

    async def start_job(self):
        logging.info("Start job called in OPC UA server.")
        await self._model.start_job()

    async def stop_job(self):
        logging.info("Stopping job called in OPC UA server.")
        await self._model.stop_job()

    def save_configuration(self, file_name: str):
        """
        Save the current configuration to a file.
        :param file_name: The file name to save the configuration to. Notice that it will be overwritten.
        """
        if not self._set_up:
            # configurations that are not set up don't need to be saved.
            logging.warning("Saving of configuration skipped: not set up.")
            return

        if os.path.isfile(file_name):
            logging.info(f"Removing previous file {file_name}.")
            os.remove(file_name)

        with open(file_name, "w") as f:
            json.dump(self._configuration, f)

        logging.info(f"Configuration written to {file_name}.")

    def get_uri(self, namespace: str) -> str:
        """Get the URI for a namespace. No check whether the namespace exists, just for the convention."""
        return "urn:" + self._configuration.company + ":opcua:" + namespace
