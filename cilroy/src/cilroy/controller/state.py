import asyncio
from asyncio import Lock
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, MutableMapping, Optional
from uuid import UUID

from cilroy.post import PostData
from cilroy.retry import Retrier
from cilroy.schedulers import Scheduler
from cilroy.status import TrainingStatus
from kilroy_face_client_py_sdk import FaceService
from kilroy_module_client_py_sdk import MetricData, ModuleService
from kilroy_server_py_utils import Observable


@dataclass
class FaceState:
    service: FaceService


@dataclass
class ModuleState:
    service: ModuleService
    archived_metrics: List[MetricData]
    metrics_stream: Observable[MetricData]
    metrics_task: asyncio.Task


@dataclass
class OfflineState:
    scrap_before: Optional[datetime]
    scrap_after: Optional[datetime]
    scrap_limit: Optional[int]


@dataclass
class OnlineState:
    cache: MutableMapping[UUID, Dict[str, Any]]
    post_scheduler: Scheduler
    post_schedulers_params: Dict[str, Dict[str, Any]]
    score_scheduler: Scheduler
    score_schedulers_params: Dict[str, Dict[str, Any]]
    lock: Lock


@dataclass
class FeedState:
    feed: List[PostData]
    length: int
    stream: Observable[PostData]


@dataclass
class RetryState:
    retrier: Retrier
    retriers_params: Dict[str, Dict[str, Any]]


@dataclass
class TrainingState:
    status: Observable[TrainingStatus]
    task: Optional[asyncio.Task]


@dataclass
class AutosaveState:
    scheduler: Scheduler
    schedulers_params: Dict[str, Dict[str, Any]]
    task: asyncio.Task


@dataclass
class State:
    face: FaceState
    module: ModuleState
    offline: OfflineState
    online: OnlineState
    training: TrainingState
    autosave: AutosaveState
    feed: FeedState
    retry: RetryState
