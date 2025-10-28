from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
import asyncio
from decimal import InvalidOperation
import inspect
import logging

from MyServer.MachineOperation import SensorType, SensorId


class SensorBase[T](ABC):
    """
    Base class for sensor types.
    """
    __namespace: str
    __name: str
    __updates_per_second: float
    __callbacks: list[Callable[[datetime, T], ...]]
    __callback_locks: dict[Callable[[datetime, T], ...], asyncio.Lock]
    __last_value: T
    __last_measured_time: datetime
    __mutator_dict: Callable[[], dict] | None = None
    __source: Callable[[...], T] | None
    __task: asyncio.Task | None

    def __init__(self, name: str, sensor_type: SensorType, identifier: int, namespace: str, updates_per_second: float):
        """
        ctor.
        :param name: Name of the sensor.
        :param identifier: Identifier of the sensor.
        :param sensor_type: Type of the sensor.
        :param namespace: Namespace of the sensor (where in the data model to be present).
        :param updates_per_second: How often the sensor is updated.
        """
        self.__name = name
        self.__namespace = namespace
        self.__callbacks: list[Callable[[datetime, T], ...]] = []
        self.__updates_per_second = updates_per_second
        self.__callback_locks: dict[Callable[[datetime, T], ...], asyncio.Lock] = {}
        self.__source = None
        self.__task = None
        self.__sensor_id: SensorId = SensorId(type=sensor_type, identifier=identifier)

    def __del__(self):
        logging.info(f"Shutting down {self.__name} (ID = {self.__sensor_id}).")
        self.stop()

    @property
    def identifier(self) -> int:
        """Get the identifier."""
        return self.__sensor_id.identifier

    @property
    def sensor_id(self) -> SensorId:
        """Get the sensor ID."""
        return self.__sensor_id

    @property
    def namespace(self) -> str:
        """The namespace of the sensor, that is, its location in the data model."""
        return self.__namespace

    @property
    def name(self) -> str:
        """The name of the sensor."""
        return self.__name

    @property
    def updates_per_second(self):
        """The updates per second."""
        return self.__updates_per_second

    @property
    def sensor_type(self) -> SensorType:
        """Get the sensor type."""
        return self.__sensor_id.type

    def to_dict(self) -> dict:
        complete_dict: dict = self._to_dict()
        if self.__mutator_dict is not None:
            complete_dict["mutator"] = self.__mutator_dict()
        return complete_dict

    @property
    def mutator_dict(self) -> Callable[[], dict]:
        return self.__mutator_dict

    @mutator_dict.setter
    def mutator_dict(self, value: Callable[[], dict]):
        self.__mutator_dict = value

    @abstractmethod
    def _to_dict(self) -> dict:
        """Create a JSON string from which the sensor can be reconstructed (but the recorded data)."""
        pass

    @abstractmethod
    def on_polling(self):
        """Is called when data is polled. Used for logging or similar actions."""
        pass

    @property
    def source(self):
        return self.__source

    @source.setter
    def source(self, value: Callable[[...], T]):
        if self.__task is not None:
            return
        self.__source = value

    @property
    def running(self):
        return self.__task is not None

    async def __poller(self):
        time_span: float = 1.0 / self.__updates_per_second
        logging.debug(f"Setting up poller (ID = {self.__sensor_id}).")
        try:
            while self.__source is not None:
                start_time: datetime = datetime.now()  # start of the full process
                self.on_polling()
                value: T = self.source()
                time: datetime = datetime.now()  # time when received - source might take a while
                await self.on_new_data(time, value)
                stop_time: datetime = datetime.now()  # awaited new data received
                time_delta: float = (stop_time - start_time).total_seconds()
                if time_delta < time_span:
                    await asyncio.sleep(time_span - time_delta)
        except Exception as e:
            logging.error(f"Error while receiving data from ID = {self.__sensor_id}: {e}")
            raise e

    def start(self):
        """Start polling the sensor."""
        logging.info(f"Starting the sensor ID = {self.__sensor_id}.")
        if self.__task is not None:
            logging.error(f"Sensor with ID = {self.__sensor_id} already running."
                          "Please call \"running\" before the start.")
            raise InvalidOperation("Task already started.")
        if self.__source is None:
            logging.error(f"Source of the sensor {self.__sensor_id} is not set.")
            return

        self.__task = asyncio.create_task(self.__poller())

    def stop(self):
        """Stop polling the sensor."""
        logging.info(f"Stopping the sensor with ID = {self.__sensor_id}.")
        if self.__task is None:
            logging.warning(f"Sensor with ID = {self.__sensor_id} was not running.")
            return
        if not self.__task.done():
            self.__task.cancel()
        self.__task = None

    async def on_new_data(self, timestamp: datetime, data: T):
        """
        To be called on new recorded data.
        :param timestamp: The recording time of the measurement.
        :param data: Recorded data.
        """
        self.__last_value = data
        self.__last_measured_time = timestamp

        # avoids potential race conditions if called again before the callback has returned
        async def safe_call(cb: Callable[[datetime, T], ...]):
            lock = self.__callback_locks.setdefault(cb, asyncio.Lock())
            async with lock:
                if inspect.iscoroutinefunction(cb):
                    await cb(timestamp, data)
                else:
                    await asyncio.to_thread(cb, timestamp, data)

        try:
            await asyncio.gather(*(safe_call(cb) for cb in self.__callbacks))
        except Exception as e:
            logging.error(f"Was not able to gather: {e.__repr__()}")
            raise e

    def add_callback(self, callback):
        """Add a callback. Can be added only once.
        :param callback: The callback to add.
        """
        if callback not in self.__callbacks:
            logging.info(f"Adding callback to sensor with ID = {self.__sensor_id}.")
            self.__callbacks.append(callback)

    def remove_callback(self, callback: Callable[[datetime, T], ...]) -> bool:
        """
        Remove a callback from the registered list.
        :param callback: The callback to be removed.
        :return: Whether the callback was removed.
        """
        if callback not in self.__callbacks:
            logging.warning(f"Trying to remove a callback from sensor with ID = {self.__sensor_id} which was not present")
            return False
        logging.info(f"Removing callback from sensor with ID = {self.__sensor_id}.")
        self.__callbacks.remove(callback)
        return True
