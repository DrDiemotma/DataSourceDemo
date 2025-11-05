from typing import Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class DriverBase[T](ABC):

    @abstractmethod
    def last_value(self) -> T:
        ...

    @abstractmethod
    def do_dict(self) -> dict[str, Any]:
        ...


