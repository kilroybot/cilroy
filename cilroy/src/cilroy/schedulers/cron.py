import asyncio
from pathlib import Path
from typing import Any, AsyncIterable, Awaitable, Callable, Dict

from cilroy.models import SerializableState
from cilroy.schedulers.base import Scheduler
from cilroy.utils import (
    seconds_until,
    next_time_from_rule,
)
from kilroy_server_py_utils import Configurable, Parameter, classproperty


class State(SerializableState):
    rule: str = "0 * * * *"


class CronScheduler(Scheduler, Configurable[State]):
    class RuleParameter(Parameter[State, str]):
        @classmethod
        async def _get(cls, state: State) -> str:
            return state.rule

        @classmethod
        async def _set(
            cls, state: State, value: str
        ) -> Callable[[], Awaitable]:
            original_value = state.rule

            async def undo():
                state.rule = original_value

            state.rule = value
            return undo

        # noinspection PyMethodParameters
        @classproperty
        def schema(cls) -> Dict[str, Any]:
            return {
                "type": "string",
                "title": cls.pretty_name,
                "default": "0 * * * *",
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
                rule = state.rule

            score_time = next_time_from_rule(rule)
            await asyncio.sleep(seconds_until(score_time))
            yield
