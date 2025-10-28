from asyncua.ua import VariantType
from typing import Any

from MyServer.MachineOperation import SensorType


def variant_type(sensor_type: SensorType) -> tuple[VariantType, Any] | None:
    """Get the variant type for OPC UA."""
    match sensor_type:
        case SensorType.TEMPERATURE | SensorType.PRESSURE:
            return VariantType.Float, 0.0

    return None