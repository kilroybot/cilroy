import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncIterable, Awaitable, Callable, Dict, Tuple
from uuid import UUID

from kilroy_server_py_utils import Configurable

from cilroy.models import SerializableState
from cilroy.posting import PostScheduler
from cilroy.utils import next_time, seconds_until, utcmidnight


class State(SerializableState):
    base: datetime = utcmidnight()
    interval: timedelta = timedelta(hours=1)


class IntervalPostScheduler(PostScheduler, Configurable[State]):
    @classmethod
    async def _save_state(cls, state: State, directory: Path) -> None:
        with open(directory / "state.json", "w") as f:
            f.write(state.json())

    async def _load_saved_state(self, directory: Path) -> State:
        with open(directory / "state.json", "r") as f:
            return State.parse_raw(f.read())

    async def run(
        self,
        generate: Callable[[], Awaitable[Tuple[UUID, Dict]]],
        post: Callable[[Dict], Awaitable[UUID]],
    ) -> AsyncIterable[Tuple[UUID, UUID]]:
        while True:
            module_post_id, post_content = await generate()

            async with self.state.read_lock() as state:
                post_time = next_time(state.base, state.interval)

            await asyncio.sleep(seconds_until(post_time))

            face_post_id = await post(post_content)

            yield module_post_id, face_post_id
