from abc import ABC, abstractmethod
from typing import TypeVar, Callable, Awaitable, Union, Optional

from kilroy_server_py_utils import Categorizable, classproperty, normalize

T = TypeVar("T")


class Retrier(Categorizable, ABC):
    # noinspection PyMethodParameters
    @classproperty
    def category(cls) -> str:
        name: str = cls.__name__
        return normalize(name.removesuffix("Retrier"))

    @abstractmethod
    async def retry(
        self,
        f: Union[Callable[..., T], Callable[..., Awaitable[T]]],
        *args,
        _on_retry: Optional[Callable[[int, float], None]] = None,
        **kwargs,
    ) -> T:
        pass
