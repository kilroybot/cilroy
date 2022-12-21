import asyncio
from asyncio import CancelledError
from typing import Any, Awaitable, Callable, Dict, TypeVar, Union, Optional

from cilroy.models import SerializableState
from cilroy.retry.base import Retrier
from kilroy_server_py_utils import Configurable, Parameter, classproperty

T = TypeVar("T")


class State(SerializableState):
    tries: Optional[int] = 3
    timeout: float = 1.0


class SimpleRetrier(Retrier, Configurable[State]):
    class TriesParameter(Parameter[State, Optional[int]]):
        # noinspection PyMethodParameters
        @classproperty
        def schema(cls) -> Dict[str, Any]:
            return {
                "type": ["integer", "null"],
                "minimum": 1,
                "title": cls.pretty_name,
                "default": 3,
            }

    class TimeoutParameter(Parameter[State, float]):
        # noinspection PyMethodParameters
        @classproperty
        def schema(cls) -> Dict[str, Any]:
            return {
                "type": "number",
                "minimum": 0.0,
                "title": cls.pretty_name,
                "default": 1.0,
            }

    async def retry(
        self,
        f: Union[Callable[..., T], Callable[..., Awaitable[T]]],
        *args,
        _on_retry: Optional[Callable[[int, float], None]] = None,
        **kwargs,
    ) -> T:
        is_coroutine = asyncio.iscoroutinefunction(f)

        async def call(f_, *args_, **kwargs_) -> T:
            if is_coroutine:
                return await f_(*args_, **kwargs_)
            else:
                return f_(*args_, **kwargs_)

        i = 0
        exceptions = []

        while True:
            async with self.state.read_lock() as state:
                tries = state.tries
                timeout = state.timeout

            try:
                return await call(f, *args, **kwargs)
            except CancelledError:
                raise
            except Exception as e:
                exceptions.append(e)
                i += 1

                if tries is not None and i >= tries:
                    raise Exception(*exceptions)

                if _on_retry is not None:
                    _on_retry(i, timeout)

                await asyncio.sleep(timeout)
