from dataclasses import dataclass

@dataclass(frozen=True)
class ServerConfiguration:
    """Configuration for a basic OPC UA server."""
    company: str
    """Company name."""
    ip_address: str
    """Local IP address."""
    fields: list[str]
    """Data fields to register."""
    port: int = 4840
    """Port of the OPC UA server."""
    device_name: str = "Device"
    """Name of the device to store data in. For human readability."""
    sensors: str = "Sensors"
