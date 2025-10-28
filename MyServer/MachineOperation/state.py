from enum import StrEnum

class State(StrEnum):
    """Describe state of the machine."""
    NORMAL = "normal"
    """Machine operates in normal mode."""
    BROKEN = "broken"
    """Machine is in broken state."""
    