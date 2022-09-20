from abc import ABC, abstractmethod
from typing import (
    AsyncIterable,
    Awaitable,
    Callable,
    Collection,
    Dict,
    Set,
)
from uuid import UUID

from kilroy_server_py_utils import Categorizable, classproperty, normalize


class ScoreScheduler(Categorizable, ABC):
    @classproperty
    def category(cls) -> str:
        name: str = cls.__name__
        return normalize(name.removesuffix("ScoreScheduler"))

    @abstractmethod
    def run(
        self,
        get_ids: Callable[[], Awaitable[Collection[UUID]]],
        score: Callable[[UUID], Awaitable[float]],
    ) -> AsyncIterable[Dict[UUID, float]]:
        pass
