import asyncio
from datetime import time
from pathlib import Path
from typing import Any, AsyncIterable, Awaitable, Callable, Dict, List

from cilroy.models import SerializableState
from cilroy.schedulers.base import Scheduler
from cilroy.utils import seconds_until, next_time_from_hours
from kilroy_server_py_utils import Configurable, Parameter, classproperty


class State(SerializableState):
    hours: List[time] = []


class TimetableScheduler(Scheduler, Configurable[State]):
    class HoursParameter(Parameter[State, List[str]]):
        @classmethod
        async def _get(cls, state: State) -> List[str]:
            return [hour.isoformat(timespec="seconds") for hour in state.hours]

        @classmethod
        async def _set(
            cls, state: State, value: List[str]
        ) -> Callable[[], Awaitable]:
            original_value = state.hours

            async def undo():
                state.hours = original_value

            state.hours = sorted([time.fromisoformat(hour) for hour in value])
            return undo

        # noinspection PyMethodParameters
        @classproperty
        def schema(cls) -> Dict[str, Any]:
            return {
                "type": "array",
                "items": {"type": "string", "format": "time"},
                "title": cls.pretty_name,
                "default": [],
            }

    @classmethod
    async def _save_state(cls, state: State, directory: Path) -> None:
        with open(directory / "state.json", "w") as f:
            f.write(state.json())

    async def _load_saved_state(self, directory: Path) -> State:
        with open(directory / "state.json", "r") as f:
            return State.parse_raw(f.read())

    async def wait(self) -> AsyncIterable[None]:
        while True:
            async with self.state.read_lock() as state:
                hours = state.hours

            score_time = next_time_from_hours(hours)
            await asyncio.sleep(seconds_until(score_time))
            yield
