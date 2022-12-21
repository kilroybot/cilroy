from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Optional, Type

from cilroy.controller.state import State
from cilroy.retry import Retrier, ExponentialBackoffRetrier
from cilroy.schedulers import Scheduler, IntervalScheduler
from kilroy_server_py_utils import (
    CategorizableBasedParameter,
    OptionalParameter,
    Parameter,
    classproperty,
)


class ScrapBeforeParameter(OptionalParameter[State, str]):
    @classmethod
    async def _get(cls, state: State) -> Optional[str]:
        if state.offline.scrap_before is None:
            return None
        return state.offline.scrap_before.isoformat()

    @classmethod
    async def _set(
        cls, state: State, value: Optional[str]
    ) -> Callable[[], Awaitable]:
        original_value = state.offline.scrap_before

        async def undo():
            state.offline.scrap_before = original_value

        state.offline.scrap_before = (
            datetime.fromisoformat(value) if value is not None else None
        )
        return undo

    # noinspection PyMethodParameters
    @classproperty
    def schema(cls) -> Dict[str, Any]:
        return {
            "type": ["string", "null"],
            "format": "date-time",
            "title": cls.pretty_name,
            "default": None,
        }


class ScrapAfterParameter(OptionalParameter[State, str]):
    @classmethod
    async def _get(cls, state: State) -> Optional[str]:
        if state.offline.scrap_after is None:
            return None
        return state.offline.scrap_after.isoformat()

    @classmethod
    async def _set(
        cls, state: State, value: Optional[str]
    ) -> Callable[[], Awaitable]:
        original_value = state.offline.scrap_after

        async def undo():
            state.offline.scrap_after = original_value

        state.offline.scrap_after = (
            datetime.fromisoformat(value) if value is not None else None
        )
        return undo

    # noinspection PyMethodParameters
    @classproperty
    def schema(cls) -> Dict[str, Any]:
        return {
            "type": ["string", "null"],
            "format": "date-time",
            "title": cls.pretty_name,
            "default": None,
        }


class ScrapLimitParameter(OptionalParameter[State, int]):
    @classmethod
    async def _get(cls, state: State) -> Optional[int]:
        if state.offline.scrap_limit is None:
            return None
        return state.offline.scrap_limit

    @classmethod
    async def _set(
        cls, state: State, value: Optional[int]
    ) -> Callable[[], Awaitable]:
        original_value = state.offline.scrap_limit

        async def undo():
            state.offline.scrap_limit = original_value

        state.offline.scrap_limit = value if value is not None else None
        return undo

    # noinspection PyMethodParameters
    @classproperty
    def schema(cls) -> Dict[str, Any]:
        return {
            "type": ["integer", "null"],
            "minimum": 0,
            "title": cls.pretty_name,
            "default": None,
        }


class PostSchedulerParameter(CategorizableBasedParameter[State, Scheduler]):
    @classmethod
    async def _get_categorizable(cls, state: State) -> Scheduler:
        return state.online.post_scheduler

    @classmethod
    async def _set_categorizable(cls, state: State, value: Scheduler) -> None:
        state.online.post_scheduler = value

    @classmethod
    async def _get_params(cls, state: State, category: str) -> Dict[str, Any]:
        return state.online.post_schedulers_params.get(category, {})

    # noinspection PyMethodParameters
    @classproperty
    def default_categorizable(cls) -> Type[Scheduler]:
        return IntervalScheduler

    # noinspection PyMethodParameters
    @classproperty
    def default_config(cls) -> Optional[Dict[str, Any]]:
        return {"interval": 3600}


class ScoreSchedulerParameter(CategorizableBasedParameter[State, Scheduler]):
    @classmethod
    async def _get_categorizable(cls, state: State) -> Scheduler:
        return state.online.score_scheduler

    @classmethod
    async def _set_categorizable(cls, state: State, value: Scheduler) -> None:
        state.online.score_scheduler = value

    @classmethod
    async def _get_params(cls, state: State, category: str) -> Dict[str, Any]:
        return state.online.score_schedulers_params.get(category, {})

    # noinspection PyMethodParameters
    @classproperty
    def default_categorizable(cls) -> Type[Scheduler]:
        return IntervalScheduler

    # noinspection PyMethodParameters
    @classproperty
    def default_config(cls) -> Optional[Dict[str, Any]]:
        return {"interval": 86400}


class AutosaveSchedulerParameter(
    CategorizableBasedParameter[State, Scheduler]
):
    @classmethod
    async def _get_categorizable(cls, state: State) -> Scheduler:
        return state.autosave.scheduler

    @classmethod
    async def _set_categorizable(cls, state: State, value: Scheduler) -> None:
        state.autosave.scheduler = value

    @classmethod
    async def _get_params(cls, state: State, category: str) -> Dict[str, Any]:
        return state.autosave.schedulers_params.get(category, {})

    # noinspection PyMethodParameters
    @classproperty
    def default_categorizable(cls) -> Type[Scheduler]:
        return IntervalScheduler

    # noinspection PyMethodParameters
    @classproperty
    def default_config(cls) -> Optional[Dict[str, Any]]:
        return {"interval": 3600}


class FeedLengthParameter(Parameter[State, int]):
    @classmethod
    async def _get(cls, state: State) -> int:
        return state.feed.length

    @classmethod
    async def _set(cls, state: State, value: int) -> Callable[[], Awaitable]:
        original_value = state.feed.length
        original_feed = state.feed.feed

        async def undo():
            state.feed.length = original_value
            state.feed.feed = original_feed

        state.feed.length = value
        state.feed.feed = state.feed.feed[-value:]
        return undo

    # noinspection PyMethodParameters
    @classproperty
    def schema(cls) -> Dict[str, Any]:
        return {
            "type": "integer",
            "minimum": 1,
            "title": cls.pretty_name,
            "default": 100,
        }


class RetrierParameter(CategorizableBasedParameter[State, Retrier]):
    @classmethod
    async def _get_categorizable(cls, state: State) -> Retrier:
        return state.retry.retrier

    @classmethod
    async def _set_categorizable(cls, state: State, value: Retrier) -> None:
        state.retry.retrier = value

    @classmethod
    async def _get_params(cls, state: State, category: str) -> Dict[str, Any]:
        return state.retry.retriers_params.get(category, {})

    # noinspection PyMethodParameters
    @classproperty
    def default_categorizable(cls) -> Type[Retrier]:
        return ExponentialBackoffRetrier
