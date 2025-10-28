from enum import StrEnum

class Mode(StrEnum):
    """Mode of the machine, that is, what is the machine currently doing."""
    IDLE = "idle"
    """Machine is idle."""
    RUNNING = "running"
    """Machine is running."""
