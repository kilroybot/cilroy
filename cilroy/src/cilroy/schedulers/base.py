from abc import ABC, abstractmethod
from typing import AsyncIterable

from kilroy_server_py_utils import Categorizable, classproperty, normalize


class Scheduler(Categorizable, ABC):
    # noinspection PyMethodParameters
    @classproperty
    def category(cls) -> str:
        name: str = cls.__name__
        return normalize(name.removesuffix("Scheduler"))

    @abstractmethod
    def wait(self) -> AsyncIterable[None]:
        pass
