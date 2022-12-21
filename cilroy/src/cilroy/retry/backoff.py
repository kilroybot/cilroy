import asyncio
from asyncio import CancelledError
from typing import Any, Awaitable, Callable, Dict, TypeVar, Union, Optional

from cilroy.models import SerializableState
from cilroy.retry.base import Retrier
from kilroy_server_py_utils import Configurable, Parameter, classproperty

T = TypeVar("T")


class State(SerializableState):
    tries: Optional[int] = 3
    delay: float = 1.0
    backoff: float = 2.0
    max_delay: Optional[float] = 60.0


class ExponentialBackoffRetrier(Retrier, Configurable[State]):
    class TriesParameter(Parameter[State, Optional[int]]):
        # noinspection PyMethodParameters
        @classproperty
        def schema(cls) -> Dict[str, Any]:
            return {
                "type": ["integer", "null"],
                "minimum": 1,
                "title": cls.pretty_name,
                "default": 10,
            }

    class DelayParameter(Parameter[State, float]):
        # noinspection PyMethodParameters
        @classproperty
        def schema(cls) -> Dict[str, Any]:
            return {
                "type": "number",
                "minimum": 0.0,
                "title": cls.pretty_name,
                "default": 1.0,
            }

    class BackoffParameter(Parameter[State, float]):
        # noinspection PyMethodParameters
        @classproperty
        def schema(cls) -> Dict[str, Any]:
            return {
                "type": "number",
                "minimum": 1.0,
                "title": cls.pretty_name,
                "default": 2.0,
            }

    class MaxDelayParameter(Parameter[State, Optional[float]]):
        # noinspection PyMethodParameters
        @classproperty
        def schema(cls) -> Dict[str, Any]:
            return {
                "type": ["number", "null"],
                "minimum": 0.0,
                "title": cls.pretty_name,
                "default": 60.0,
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

        async with self.state.read_lock() as state:
            delay = state.delay

        while True:
            async with self.state.read_lock() as state:
                tries = state.tries
                backoff = state.backoff
                max_delay = state.max_delay

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
                    _on_retry(i, delay)

                await asyncio.sleep(delay)

                delay = delay * backoff
                if max_delay is not None:
                    delay = min(delay, max_delay)
