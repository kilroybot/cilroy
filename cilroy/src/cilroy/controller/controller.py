import asyncio
import json
import logging
from abc import ABC, abstractmethod
from asyncio import Lock
from copy import deepcopy
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    Dict,
    List,
    Mapping,
    Set,
    Tuple,
    Type,
    Optional,
)
from uuid import UUID

from aiostream.aiter_utils import anext
from grpclib.client import Channel

from cilroy.controller.parameters import (
    PostSchedulerParameter,
    ScoreSchedulerParameter,
    ScrapAfterParameter,
    ScrapBeforeParameter,
    ScrapLimitParameter,
    FeedLengthParameter,
    RetrierParameter,
    AutosaveSchedulerParameter,
)
from cilroy.controller.params import (
    OfflineParams,
    OnlineParams,
    Params,
    FaceParams,
    ModuleParams,
    FeedParams,
    RetryParams,
    AutosaveParams,
)
from cilroy.controller.state import (
    OfflineState,
    OnlineState,
    State,
    FaceState,
    ModuleState,
    FeedState,
    RetryState,
    TrainingState,
    AutosaveState,
)
from cilroy.messages import Status
from cilroy.metadata import Metadata
from cilroy.post import PostData
from cilroy.retry import Retrier, SimpleRetrier
from cilroy.schedulers import Scheduler
from cilroy.status import TrainingStatus
from kilroy_face_client_py_sdk import FaceService
from kilroy_module_client_py_sdk import MetricConfig, MetricData, ModuleService
from kilroy_server_py_utils import (
    Configurable,
    JSONSchema,
    Observable,
    Parameter,
    ReadOnlyObservableWrapper,
    ReadableObservable,
    classproperty,
    Configuration,
)

logger = logging.getLogger(__name__)


class CilroyControllerBase(Configurable[State], ABC):
    def __init__(
        self, config: Configuration[State], state_directory: Path, **kwargs
    ) -> None:
        self._state_directory = state_directory
        super().__init__(config, **kwargs)

    @staticmethod
    async def _build_face_service(params: FaceParams) -> FaceService:
        return FaceService(Channel(params.host, params.port))

    @classmethod
    async def _build_face_state(cls, params: FaceParams) -> FaceState:
        return FaceState(
            service=await cls._build_face_service(params),
        )

    @staticmethod
    async def _build_module_service(params: ModuleParams) -> ModuleService:
        return ModuleService(Channel(params.host, params.port))

    async def _build_module_state(self, params: ModuleParams) -> ModuleState:
        return ModuleState(
            service=await self._build_module_service(params),
            archived_metrics=[],
            metrics_stream=await Observable.build(),
            metrics_task=asyncio.create_task(self._watch_metrics_task()),
        )

    @staticmethod
    async def _build_offline_state(params: OfflineParams) -> OfflineState:
        return OfflineState(
            scrap_limit=params.scrap_limit,
            scrap_before=params.scrap_before,
            scrap_after=params.scrap_after,
        )

    @classmethod
    async def _build_post_scheduler(cls, params: OnlineParams) -> Scheduler:
        return await cls._build_categorizable(
            Scheduler,
            params.post_scheduler_type,
            **params.post_schedulers_params.get(
                params.post_scheduler_type, {}
            ),
        )

    @classmethod
    async def _build_score_scheduler(cls, params: OnlineParams) -> Scheduler:
        return await cls._build_categorizable(
            Scheduler,
            params.score_scheduler_type,
            **params.score_schedulers_params.get(
                params.score_scheduler_type, {}
            ),
        )

    @classmethod
    async def _build_online_state(cls, params: OnlineParams) -> OnlineState:
        return OnlineState(
            cache={},
            post_scheduler=await cls._build_post_scheduler(params),
            post_schedulers_params=params.post_schedulers_params,
            score_scheduler=await cls._build_score_scheduler(params),
            score_schedulers_params=params.score_schedulers_params,
            lock=Lock(),
        )

    @staticmethod
    async def _build_training_status() -> Observable[TrainingStatus]:
        return await Observable.build(TrainingStatus.IDLE)

    @staticmethod
    async def _build_feed_state(params: FeedParams) -> FeedState:
        return FeedState(
            feed=[],
            length=params.length,
            stream=await Observable.build(),
        )

    @classmethod
    async def _build_retrier(cls, params: RetryParams) -> Retrier:
        return await cls._build_categorizable(
            Retrier,
            params.retrier_type,
            **params.retriers_params.get(params.retrier_type, {}),
        )

    @classmethod
    async def _build_retry_state(cls, params: RetryParams) -> RetryState:
        return RetryState(
            retrier=await cls._build_retrier(params),
            retriers_params=params.retriers_params,
        )

    async def _build_training_state(self) -> TrainingState:
        return TrainingState(
            task=None, status=await self._build_training_status()
        )

    @classmethod
    async def _build_autosave_scheduler(
        cls, params: AutosaveParams
    ) -> Scheduler:
        return await cls._build_categorizable(
            Scheduler,
            params.scheduler_type,
            **params.schedulers_params.get(params.scheduler_type, {}),
        )

    async def _build_autosave_state(
        self, params: AutosaveParams
    ) -> AutosaveState:
        return AutosaveState(
            scheduler=await self._build_autosave_scheduler(params),
            schedulers_params=params.schedulers_params,
            task=asyncio.create_task(self._autosave_task()),
        )

    async def _build_default_state(self) -> State:
        params = Params(**self._kwargs)
        return State(
            face=await self._build_face_state(params.face),
            module=await self._build_module_state(params.module),
            offline=await self._build_offline_state(params.offline),
            online=await self._build_online_state(params.online),
            training=await self._build_training_state(),
            autosave=await self._build_autosave_state(params.autosave),
            feed=await self._build_feed_state(params.feed),
            retry=await self._build_retry_state(params.retry),
        )

    @staticmethod
    async def _save_face_state(state: FaceState, directory: Path) -> None:
        pass

    @staticmethod
    async def _save_module_metrics(
        metrics: List[MetricData], directory: Path
    ) -> None:
        serialized = [json.loads(metric.json()) for metric in metrics]
        with open(directory / "metrics.json", "w") as f:
            json.dump([metric for metric in serialized], f)

    @classmethod
    async def _save_module_state(
        cls, state: ModuleState, directory: Path
    ) -> None:
        metrics_directory = directory / "metrics"
        metrics_directory.mkdir(parents=True, exist_ok=True)
        await cls._save_module_metrics(
            state.archived_metrics, metrics_directory
        )

    @staticmethod
    async def _create_offline_state_dict(
        state: OfflineState,
    ) -> Dict[str, Any]:
        return {
            "scrap_limit": state.scrap_limit,
            "scrap_before": state.scrap_before.isoformat()
            if state.scrap_before is not None
            else None,
            "scrap_after": state.scrap_after.isoformat()
            if state.scrap_after is not None
            else None,
        }

    @classmethod
    async def _save_offline_state(
        cls, state: OfflineState, directory: Path
    ) -> None:
        state_dict = await cls._create_offline_state_dict(state)
        await cls._save_state_dict(state_dict, directory)

    @staticmethod
    async def _serialize_online_cache(
        cache: Mapping[UUID, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        return {str(k): v for k, v in cache.items()}

    @staticmethod
    async def _deserialize_online_cache(
        cache: Mapping[str, Dict[str, Any]]
    ) -> Dict[UUID, Dict[str, Any]]:
        return {UUID(k): v for k, v in cache.items()}

    @classmethod
    async def _create_online_state_dict(
        cls,
        state: OnlineState,
    ) -> Dict[str, Any]:
        return {
            "cache": await cls._serialize_online_cache(state.cache),
            "post_scheduler_type": state.post_scheduler.category,
            "post_schedulers_params": state.post_schedulers_params,
            "score_scheduler_type": state.score_scheduler.category,
            "score_schedulers_params": state.score_schedulers_params,
        }

    @staticmethod
    async def _save_post_scheduler(
        scheduler: Scheduler, directory: Path
    ) -> None:
        if isinstance(scheduler, Configurable):
            await scheduler.save(directory)

    @staticmethod
    async def _save_score_scheduler(
        scheduler: Scheduler, directory: Path
    ) -> None:
        if isinstance(scheduler, Configurable):
            await scheduler.save(directory)

    @classmethod
    async def _save_online_state(
        cls, state: OnlineState, directory: Path
    ) -> None:
        post_scheduler_dir = directory / "post_scheduler"
        post_scheduler_dir.mkdir(parents=True, exist_ok=True)
        await cls._save_post_scheduler(
            state.post_scheduler, post_scheduler_dir
        )

        score_scheduler_dir = directory / "score_scheduler"
        score_scheduler_dir.mkdir(parents=True, exist_ok=True)
        await cls._save_score_scheduler(
            state.score_scheduler, score_scheduler_dir
        )

        state_dict = await cls._create_online_state_dict(state)
        await cls._save_state_dict(state_dict, directory)

    @staticmethod
    async def _save_autosave_scheduler(
        scheduler: Scheduler, directory: Path
    ) -> None:
        if isinstance(scheduler, Configurable):
            await scheduler.save(directory)

    @classmethod
    async def _create_autosave_state_dict(
        cls,
        state: AutosaveState,
    ) -> Dict[str, Any]:
        return {
            "scheduler_type": state.scheduler.category,
            "schedulers_params": state.schedulers_params,
        }

    @classmethod
    async def _save_autosave_state(
        cls, state: AutosaveState, directory: Path
    ) -> None:
        scheduler_dir = directory / "scheduler"
        scheduler_dir.mkdir(parents=True, exist_ok=True)
        await cls._save_autosave_scheduler(state.scheduler, scheduler_dir)

        state_dict = await cls._create_autosave_state_dict(state)
        await cls._save_state_dict(state_dict, directory)

    @classmethod
    async def _save_feed_state(cls, state: FeedState, directory: Path) -> None:
        serialized_feed = [json.loads(post.json()) for post in state.feed]
        state_dict = {
            "feed": serialized_feed,
            "length": state.length,
        }
        await cls._save_state_dict(state_dict, directory)

    @staticmethod
    async def _save_retrier(retrier: Retrier, directory: Path) -> None:
        if isinstance(retrier, Configurable):
            await retrier.save(directory)

    @classmethod
    async def _create_retry_state_dict(
        cls,
        state: RetryState,
    ) -> Dict[str, Any]:
        return {
            "retrier_type": state.retrier.category,
            "retriers_params": state.retriers_params,
        }

    @classmethod
    async def _save_retry_state(
        cls, state: RetryState, directory: Path
    ) -> None:
        retrier_dir = directory / "retrier"
        retrier_dir.mkdir(parents=True, exist_ok=True)
        await cls._save_retrier(state.retrier, retrier_dir)

        state_dict = await cls._create_retry_state_dict(state)
        await cls._save_state_dict(state_dict, directory)

    @classmethod
    async def _save_state(cls, state: State, directory: Path) -> None:
        face_directory = directory / "face"
        face_directory.mkdir(parents=True, exist_ok=True)
        await cls._save_face_state(state.face, face_directory)

        module_directory = directory / "module"
        module_directory.mkdir(parents=True, exist_ok=True)
        await cls._save_module_state(state.module, module_directory)

        offline_directory = directory / "offline"
        offline_directory.mkdir(parents=True, exist_ok=True)
        await cls._save_offline_state(state.offline, offline_directory)

        online_directory = directory / "online"
        online_directory.mkdir(parents=True, exist_ok=True)
        await cls._save_online_state(state.online, online_directory)

        autosave_directory = directory / "autosave"
        autosave_directory.mkdir(parents=True, exist_ok=True)
        await cls._save_autosave_state(state.autosave, autosave_directory)

        feed_directory = directory / "feed"
        feed_directory.mkdir(parents=True, exist_ok=True)
        await cls._save_feed_state(state.feed, feed_directory)

        retrier_directory = directory / "retry"
        retrier_directory.mkdir(parents=True, exist_ok=True)
        await cls._save_retry_state(state.retry, retrier_directory)

    # noinspection PyUnusedLocal
    @classmethod
    async def _load_saved_face_state(
        cls, directory: Path, params: FaceParams
    ) -> FaceState:
        return FaceState(service=await cls._build_face_service(params))

    @staticmethod
    async def _load_module_metrics(directory: Path) -> List[MetricData]:
        with open(directory / "metrics.json", "r") as f:
            serialized = json.load(f)
        return [MetricData.parse_obj(metric) for metric in serialized]

    async def _load_saved_module_state(
        self, directory: Path, params: ModuleParams
    ) -> ModuleState:
        return ModuleState(
            service=await self._build_module_service(params),
            archived_metrics=await self._load_module_metrics(
                directory / "metrics"
            ),
            metrics_stream=await Observable.build(),
            metrics_task=asyncio.create_task(self._watch_metrics_task()),
        )

    @classmethod
    async def _load_saved_offline_state(
        cls, directory: Path, params: OfflineParams
    ) -> OfflineState:
        state_dict = await cls._load_state_dict(directory)

        if "scrap_before" in state_dict:
            if state_dict["scrap_before"] is None:
                scrap_before = None
            else:
                scrap_before = datetime.fromisoformat(
                    state_dict["scrap_before"]
                )
        else:
            scrap_before = params.scrap_before

        if "scrap_after" in state_dict:
            if state_dict["scrap_after"] is None:
                scrap_after = None
            else:
                scrap_after = datetime.fromisoformat(state_dict["scrap_after"])
        else:
            scrap_after = params.scrap_after

        return OfflineState(
            scrap_limit=state_dict.get("scrap_limit", params.scrap_limit),
            scrap_before=scrap_before,
            scrap_after=scrap_after,
        )

    @classmethod
    async def _load_saved_post_scheduler(
        cls,
        directory: Path,
        state_dict: Dict[str, Any],
        params: OnlineParams,
    ) -> Scheduler:
        return await cls._load_generic(
            directory,
            Scheduler,
            category=state_dict.get(
                "post_scheduler_type", params.post_scheduler_type
            ),
            default=partial(
                cls._build_post_scheduler,
                params,
            ),
        )

    @classmethod
    async def _load_saved_score_scheduler(
        cls,
        directory: Path,
        state_dict: Dict[str, Any],
        params: OnlineParams,
    ) -> Scheduler:
        return await cls._load_generic(
            directory,
            Scheduler,
            category=state_dict.get(
                "score_scheduler_type", params.score_scheduler_type
            ),
            default=partial(
                cls._build_score_scheduler,
                params,
            ),
        )

    @classmethod
    async def _load_saved_online_state(
        cls, directory: Path, params: OnlineParams
    ) -> OnlineState:
        state_dict = await cls._load_state_dict(directory)
        return OnlineState(
            cache=await cls._deserialize_online_cache(
                state_dict.get("cache", {})
            ),
            post_scheduler=await cls._load_saved_post_scheduler(
                directory / "post_scheduler",
                state_dict,
                params,
            ),
            post_schedulers_params=state_dict.get(
                "post_schedulers_params", params.post_schedulers_params
            ),
            score_scheduler=await cls._load_saved_score_scheduler(
                directory / "score_scheduler",
                state_dict,
                params,
            ),
            score_schedulers_params=state_dict.get(
                "score_schedulers_params", params.score_schedulers_params
            ),
            lock=Lock(),
        )

    @classmethod
    async def _load_saved_autosave_scheduler(
        cls,
        directory: Path,
        state_dict: Dict[str, Any],
        params: AutosaveParams,
    ) -> Scheduler:
        return await cls._load_generic(
            directory,
            Scheduler,
            category=state_dict.get("scheduler_type", params.scheduler_type),
            default=partial(
                cls._build_autosave_scheduler,
                params,
            ),
        )

    async def _load_saved_autosave_state(
        self, directory: Path, params: AutosaveParams
    ) -> AutosaveState:
        state_dict = await self._load_state_dict(directory)
        return AutosaveState(
            scheduler=await self._load_saved_autosave_scheduler(
                directory / "scheduler",
                state_dict,
                params,
            ),
            schedulers_params=state_dict.get(
                "schedulers_params", params.schedulers_params
            ),
            task=asyncio.create_task(self._autosave_task()),
        )

    @classmethod
    async def _load_saved_feed_state(
        cls, directory: Path, params: FeedParams
    ) -> FeedState:
        state_dict = await cls._load_state_dict(directory)
        return FeedState(
            feed=[
                PostData.parse_obj(post) for post in state_dict.get("feed", [])
            ],
            length=state_dict.get("length", params.length),
            stream=await Observable.build(),
        )

    @classmethod
    async def _load_saved_retrier(
        cls,
        directory: Path,
        state_dict: Dict[str, Any],
        params: RetryParams,
    ) -> Retrier:
        return await cls._load_generic(
            directory,
            Retrier,
            category=state_dict.get("retrier_type", params.retrier_type),
            default=partial(
                cls._build_retrier,
                params,
            ),
        )

    @classmethod
    async def _load_saved_retry_state(
        cls, directory: Path, params: RetryParams
    ) -> RetryState:
        state_dict = await cls._load_state_dict(directory)
        return RetryState(
            retrier=await cls._load_saved_retrier(
                directory / "retrier",
                state_dict,
                params,
            ),
            retriers_params=state_dict.get(
                "retriers_params",
                params.retriers_params.get(params.retrier_type),
            ),
        )

    async def _load_saved_state(self, directory: Path) -> State:
        params = Params(**self._kwargs)
        return State(
            face=await self._load_saved_face_state(
                directory / "face", params.face
            ),
            module=await self._load_saved_module_state(
                directory / "module", params.module
            ),
            offline=await self._load_saved_offline_state(
                directory / "offline", params.offline
            ),
            online=await self._load_saved_online_state(
                directory / "online", params.online
            ),
            training=await self._build_training_state(),
            autosave=await self._load_saved_autosave_state(
                directory / "autosave", params.autosave
            ),
            feed=await self._load_saved_feed_state(
                directory / "feed", params.feed
            ),
            retry=await self._load_saved_retry_state(
                directory / "retry", params.retry
            ),
        )

    async def cleanup(self) -> None:
        async with self.state.write_lock() as state:
            if isinstance(state.online.post_scheduler, Configurable):
                await state.online.post_scheduler.cleanup()
            if isinstance(state.online.score_scheduler, Configurable):
                await state.online.score_scheduler.cleanup()
            if isinstance(state.autosave.scheduler, Configurable):
                await state.autosave.scheduler.cleanup()
            if isinstance(state.retry.retrier, Configurable):
                await state.retry.retrier.cleanup()
            state.module.metrics_task.cancel()
            try:
                await state.module.metrics_task
            except asyncio.CancelledError:
                pass

    # noinspection PyMethodParameters
    @classproperty
    def parameters(cls) -> Set[Type[Parameter]]:
        return {
            ScrapBeforeParameter,
            ScrapAfterParameter,
            ScrapLimitParameter,
            PostSchedulerParameter,
            ScoreSchedulerParameter,
            AutosaveSchedulerParameter,
            FeedLengthParameter,
            RetrierParameter,
        }

    @abstractmethod
    async def _watch_metrics_task(self) -> None:
        pass

    @abstractmethod
    async def _autosave_task(self) -> None:
        pass


class CilroyControllerDelegatedBase(CilroyControllerBase, ABC):
    async def get_face_metadata(self) -> Metadata:
        async with self.state.read_lock() as state:
            metadata = await state.face.service.get_metadata()
            return Metadata(key=metadata.key, description=metadata.description)

    async def get_module_metadata(self) -> Metadata:
        async with self.state.read_lock() as state:
            metadata = await state.module.service.get_metadata()
            return Metadata(key=metadata.key, description=metadata.description)

    async def get_face_post_schema(self) -> JSONSchema:
        async with self.state.read_lock() as state:
            return JSONSchema(**await state.face.service.get_post_schema())

    async def get_module_post_schema(self) -> JSONSchema:
        async with self.state.read_lock() as state:
            return JSONSchema(**await state.module.service.get_post_schema())

    async def get_face_status(self) -> Status:
        async with self.state.read_lock() as state:
            status = await state.face.service.get_status()
        return Status(status)

    async def watch_face_status(self) -> AsyncIterable[Status]:
        async with self.state.read_lock() as state:
            service = state.face.service
        async for status in service.watch_status():
            yield Status(status)

    async def get_module_status(self) -> Status:
        async with self.state.read_lock() as state:
            status = await state.module.service.get_status()
        return Status(status)

    async def watch_module_status(self) -> AsyncIterable[Status]:
        async with self.state.read_lock() as state:
            service = state.module.service
        async for status in service.watch_status():
            yield Status(status)

    async def get_face_config_schema(self) -> JSONSchema:
        async with self.state.read_lock() as state:
            return JSONSchema(**await state.face.service.get_config_schema())

    async def get_face_config(self) -> Dict[str, Any]:
        async with self.state.read_lock() as state:
            return await state.face.service.get_config()

    async def watch_face_config(self) -> AsyncIterable[Dict[str, Any]]:
        async with self.state.read_lock() as state:
            service = state.face.service
        async for config in service.watch_config():
            yield config

    async def set_face_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        async with self.state.write_lock() as state:
            return await state.face.service.set_config(config)

    async def get_module_config_schema(self) -> JSONSchema:
        async with self.state.read_lock() as state:
            return JSONSchema(**await state.module.service.get_config_schema())

    async def get_module_config(self) -> Dict[str, Any]:
        async with self.state.read_lock() as state:
            return await state.module.service.get_config()

    async def watch_module_config(self) -> AsyncIterable[Dict[str, Any]]:
        async with self.state.read_lock() as state:
            service = state.module.service
        async for config in service.watch_config():
            yield config

    async def reset_face(self) -> None:
        logger.info("Resetting face...")
        async with self.state.write_lock() as state:
            await state.face.service.reset()
        logger.info("Face reset.")

    async def save_face(self) -> None:
        logger.info("Saving face...")
        async with self.state.write_lock() as state:
            await state.face.service.save()
        logger.info("Face saved.")

    async def save_module(self) -> None:
        logger.info("Saving module...")
        async with self.state.write_lock() as state:
            await state.module.service.save()
        logger.info("Module saved.")

    async def generate_posts(self, n: int) -> AsyncIterable[Dict[str, Any]]:
        async with self.state.read_lock() as state:
            service = state.module.service

        async for content, _ in service.generate(n):
            yield content


class CilroyController(CilroyControllerDelegatedBase):
    async def get_training_status(self) -> ReadableObservable[TrainingStatus]:
        async with self.state.read_lock() as state:
            return ReadOnlyObservableWrapper(state.training.status)

    async def _train_offline_fit(
        self, data: AsyncIterable[Tuple[Dict[str, Any], float]]
    ) -> None:
        async with self.state.read_lock() as state:
            service: ModuleService = state.module.service
            retrier: Retrier = state.retry.retrier

        await retrier.retry(
            service.fit_supervised,
            data,
            _on_retry=lambda number, timeout: logger.warning(
                f"Offline training: "
                f"Retrying fitting posts after {timeout} seconds "
                f"(retry number {number})."
            ),
        )

    async def _train_offline(self) -> None:
        logger.info("Offline training started.")

        async def __map_data(
            _posts: AsyncIterable[Tuple[UUID, Dict, float]]
        ) -> AsyncIterable[Tuple[Dict, float]]:
            async for _, post, score in _posts:
                yield post, score

        state = await self.state.value.fetch()
        data = state.face.service.scrap(
            state.offline.scrap_limit,
            state.offline.scrap_before,
            state.offline.scrap_after,
        )
        data = __map_data(data)

        try:
            await self._train_offline_fit(data)
        except Exception as e:
            logger.error(f"Offline training failed! Stopping...", exc_info=e)

        async with self.state.write_lock() as state:
            await state.training.status.set(TrainingStatus.IDLE)
            state.training.task = None

        logger.info("Offline training finished.")

    async def train_offline(self) -> None:
        async with self.state.write_lock() as state:
            if state.training.task is not None:
                raise RuntimeError("Training is already in progress.")
            await state.training.status.set(TrainingStatus.OFFLINE)
            state.training.task = asyncio.create_task(self._train_offline())

    async def _train_online_post_loop(self) -> None:
        async with self.state.read_lock() as state:
            module_service = state.module.service
            face_service = state.face.service
            post_scheduler = state.online.post_scheduler
            lock = state.online.lock
            retrier = state.retry.retrier

        async def __call_generate() -> Tuple[Dict[str, Any], Dict[str, Any]]:
            return await anext(module_service.generate())

        async def __call_post(post_) -> Tuple[UUID, Optional[str]]:
            return await face_service.post(post_)

        async def __generate_and_post() -> Tuple[
            UUID, Dict[str, Any], str, Dict[str, Any]
        ]:
            content, metadata = await retrier.retry(
                __call_generate,
                _on_retry=lambda number, timeout: logger.warning(
                    f"Online training: "
                    f"Retrying generating post after {timeout} seconds "
                    f"(retry number {number})."
                ),
            )
            id, url = await retrier.retry(
                __call_post,
                content,
                _on_retry=lambda number, timeout: logger.warning(
                    f"Online training: "
                    f"Retrying posting after {timeout} seconds "
                    f"(retry number {number})."
                ),
            )
            return id, content, url, metadata

        infinite_retrier = await SimpleRetrier.create(tries=None, timeout=1)

        async for _ in post_scheduler.wait():
            async with lock:
                logger.info("Online training: Creating new post...")

                id, content, url, metadata = await infinite_retrier.retry(
                    __generate_and_post,
                    _on_retry=lambda number, timeout: logger.warning(
                        f"Online training: "
                        f"Retrying generating and posting "
                        f"after {timeout} seconds (retry number {number})."
                    ),
                )

                post = PostData(
                    id=id,
                    url=url,
                    content=content,
                    created_at=datetime.utcnow(),
                )

                async with self.state.write_lock() as state:
                    state.online.cache[id] = {
                        "content": content,
                        "metadata": metadata,
                    }
                    state.feed.feed = state.feed.feed + [post]
                    state.feed.feed = state.feed.feed[-state.feed.length :]
                    await state.feed.stream.set(post)

                logger.info(f"Online training: New post with id {str(id)}.")

    async def _train_online_fit(
        self, data: AsyncIterable[Tuple[Dict[str, Any], Dict[str, Any], float]]
    ) -> None:
        async with self.state.read_lock() as state:
            service = state.module.service
            retrier = state.retry.retrier

        await retrier.retry(
            service.fit_reinforced,
            data,
            _on_retry=lambda number, timeout: logger.warning(
                f"Online training: "
                f"Retrying fitting scores after {timeout} seconds "
                f"(retry number {number})."
            ),
        )

    async def _train_online_score_loop(self) -> None:
        async with self.state.read_lock() as state:
            face = state.face.service
            scheduler = state.online.score_scheduler
            lock = state.online.lock
            retrier = state.retry.retrier

        async def __score(id: UUID) -> float:
            return await retrier.retry(
                face.score,
                id,
                _on_retry=lambda number, timeout: logger.warning(
                    f"Online training: "
                    f"Retrying scoring post with id {str(id)} "
                    f"after {timeout} seconds (retry number {number})."
                ),
            )

        async def __get_data() -> AsyncIterable[
            Tuple[Dict[str, Any], Dict[str, Any], float]
        ]:
            async with self.state.read_lock() as state:
                keys = list(state.online.cache.keys())

            for key in keys:
                async with self.state.write_lock() as state:
                    value = state.online.cache.pop(key)

                score = await __score(key)
                yield value["content"], value["metadata"], score

        async for _ in scheduler.wait():
            async with lock:
                logger.info("Online training: Fitting scores...")
                await self._train_online_fit(__get_data())
                logger.info("Online training: Scores fitted.")

    async def _train_online(self) -> None:
        logger.info("Online training started.")

        tasks = [
            asyncio.create_task(self._train_online_post_loop()),
            asyncio.create_task(self._train_online_score_loop()),
        ]
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Online training failed! Stopping...", exc_info=e)
        finally:
            for task in tasks:
                task.cancel()

        async with self.state.write_lock() as state:
            await state.training.status.set(TrainingStatus.IDLE)
            state.training.task = None

        logger.info("Online training finished.")

    async def train_online(self) -> None:
        async with self.state.write_lock() as state:
            if state.training.task is not None:
                raise RuntimeError("Training is already in progress.")
            await state.training.status.set(TrainingStatus.ONLINE)
            state.training.task = asyncio.create_task(self._train_online())

    async def stop_training(self) -> None:
        async with self.state.write_lock() as state:
            if state.training.task is not None:
                state.training.task.cancel()
                try:
                    await state.training.task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.warning("Training task failed.", exc_info=e)
                state.training.task = None
                await state.training.status.set(TrainingStatus.IDLE)
                logger.info("Training stopped.")

    async def get_module_metrics_config(self) -> List[MetricConfig]:
        async with self.state.read_lock() as state:
            return await state.module.service.get_metrics_config()

    async def get_module_metrics(self) -> List[MetricData]:
        async with self.state.read_lock() as state:
            return state.module.archived_metrics

    async def _watch_metrics_task(self) -> None:
        async with self.state.read_lock() as state:
            service: ModuleService = state.module.service

        while True:
            try:
                async for metric in service.watch_metrics():
                    async with self.state.write_lock() as state:
                        state.module.archived_metrics.append(metric)
                        await state.module.metrics_stream.set(metric)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning("Metrics stream failed.", exc_info=e)
                await asyncio.sleep(1)

    async def _autosave_task(self) -> None:
        async with self.state.read_lock() as state:
            scheduler = state.autosave.scheduler

        async for _ in scheduler.wait():
            try:
                await self.save_self(self._state_directory)
                await self.save_face()
                await self.save_module()
            except Exception as e:
                logger.warning("Autosave failed.", exc_info=e)

    async def watch_module_metrics(self) -> AsyncIterator[MetricData]:
        async with self.state.read_lock() as state:
            metrics = state.module.metrics_stream
        async for metric in metrics.subscribe():
            yield metric

    async def _reset_metrics_task(self, state: State) -> None:
        state.module.metrics_task.cancel()
        try:
            await state.module.metrics_task
        except asyncio.CancelledError:
            pass
        state.module.metrics_task = asyncio.create_task(
            self._watch_metrics_task()
        )

    async def set_module_config(
        self, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        async with self.state.write_lock() as state:
            new = await state.module.service.set_config(config)
            await self._reset_metrics_task(state)
            return new

    async def reset_self(self) -> None:
        logger.info("Resetting state...")
        await self.cleanup()
        await self.init()
        logger.info("State reset.")

    async def reset_module(self) -> None:
        logger.info("Resetting module...")
        await self.stop_training()
        async with self.state.write_lock() as state:
            await state.module.service.reset()
            state.module.archived_metrics = []
            state.online.cache.clear()
            state.feed.feed = []
            await self._reset_metrics_task(state)
        logger.info("Module reset.")

    async def save_self(self, directory: Path) -> None:
        logger.info("Saving state...")
        await self.save(directory)
        logger.info("State saved.")

    async def get_feed(self) -> AsyncIterable[PostData]:
        async with self.state.read_lock() as state:
            feed = deepcopy(state.feed.feed)

        for post in feed:
            yield post

    async def watch_feed(self) -> AsyncIterable[PostData]:
        async with self.state.read_lock() as state:
            feed = state.feed.stream
        async for post in feed.subscribe():
            yield post
