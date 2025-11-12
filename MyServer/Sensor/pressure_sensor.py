from MyServer.MachineOperation import SensorType
from MyServer.Sensor.Base.sensor_base import SensorBase, SensorDictBase


class PressureSensor(SensorBase[float]):
    """Pressure sensor implementation."""

    def __init__(self,
                 identifier: int,
                 namespace = "Sensors",
                 updates_per_second: float = 0.5):
        super().__init__(f"Pressure_sensor_{identifier:03d}",
                         identifier=identifier,
                         sensor_type=SensorType.PRESSURE,
                         namespace=namespace,
                         updates_per_second=updates_per_second)

    def _to_data_dictionary(self) -> SensorDictBase:
        d : SensorDictBase = SensorDictBase(
            sensor_type=SensorType.PRESSURE,
            identifier=self.identifier,
            namespace=self.namespace,
            updates_per_second=self.updates_per_second
        )

        return d

    def on_polling(self):
        pass  # currently nothing to do here