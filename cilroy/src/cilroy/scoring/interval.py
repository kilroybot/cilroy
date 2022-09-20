import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncIterable, Awaitable, Callable, Collection, Dict
from uuid import UUID

from kilroy_server_py_utils import Configurable

from cilroy.models import SerializableState
from cilroy.scoring import ScoreScheduler
from cilroy.utils import next_time, seconds_until, utcmidnight


class State(SerializableState):
    base: datetime = utcmidnight()
    interval: timedelta = timedelta(days=1)


class IntervalScoreScheduler(ScoreScheduler, Configurable[State]):
    @classmethod
    async def _save_state(cls, state: State, directory: Path) -> None:
        with open(directory / "state.json", "w") as f:
            f.write(state.json())

    async def _load_saved_state(self, directory: Path) -> State:
        with open(directory / "state.json", "r") as f:
            return State.parse_raw(f.read())

    async def run(
        self,
        get_ids: Callable[[], Awaitable[Collection[UUID]]],
        score: Callable[[UUID], Awaitable[float]],
    ) -> AsyncIterable[Dict[UUID, float]]:
        while True:
            async with self.state.read_lock() as state:
                score_time = next_time(state.base, state.interval)

            await asyncio.sleep(seconds_until(score_time))

            ids = await get_ids()
            scores = {post_id: await score(post_id) for post_id in ids}
            yield scores
