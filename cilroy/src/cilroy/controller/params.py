from datetime import datetime
from typing import Any, Dict, Optional

from cilroy.models import SerializableModel
from cilroy.retry import ExponentialBackoffRetrier
from cilroy.schedulers import IntervalScheduler


class FaceParams(SerializableModel):
    host: str = "localhost"
    port: int = 10000


class ModuleParams(SerializableModel):
    host: str = "localhost"
    port: int = 11000


class OfflineParams(SerializableModel):
    scrap_before: Optional[datetime] = None
    scrap_after: Optional[datetime] = None
    scrap_limit: Optional[int] = None


class OnlineParams(SerializableModel):
    post_scheduler_type: str = IntervalScheduler.category
    post_schedulers_params: Dict[str, Dict[str, Any]] = {
        "interval": {"interval": 3600},
    }
    score_scheduler_type: str = IntervalScheduler.category
    score_schedulers_params: Dict[str, Dict[str, Any]] = {
        "interval": {"interval": 86400},
    }


class AutosaveParams(SerializableModel):
    scheduler_type: str = IntervalScheduler.category
    schedulers_params: Dict[str, Dict[str, Any]] = {
        "interval": {"interval": 3600},
    }


class FeedParams(SerializableModel):
    length: int = 100


class RetryParams(SerializableModel):
    retrier_type: str = ExponentialBackoffRetrier.category
    retriers_params: Dict[str, Dict[str, Any]] = {}


class Params(SerializableModel):
    face: FaceParams = FaceParams()
    module: ModuleParams = ModuleParams()
    offline: OfflineParams = OfflineParams()
    online: OnlineParams = OnlineParams()
    autosave: AutosaveParams = AutosaveParams()
    feed: FeedParams = FeedParams()
    retry: RetryParams = RetryParams()
