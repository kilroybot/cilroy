from dataclasses import dataclass
from typing import List

import betterproto


class Status(betterproto.Enum):
    """Possible service statuses."""

    STATUS_UNSPECIFIED = 0
    STATUS_LOADING = 1
    STATUS_READY = 2


class TrainingStatus(betterproto.Enum):
    """Possible training statuses."""

    TRAINING_STATUS_UNSPECIFIED = 0
    TRAINING_STATUS_IDLE = 1
    TRAINING_STATUS_OFFLINE = 2
    TRAINING_STATUS_ONLINE = 3


@dataclass(eq=False, repr=False)
class GetFaceMetadataRequest(betterproto.Message):
    """Request for GetFaceMetadata."""

    pass


@dataclass(eq=False, repr=False)
class GetFaceMetadataResponse(betterproto.Message):
    """Response from GetFaceMetadata."""

    key: str = betterproto.string_field(1)
    description: str = betterproto.string_field(2)


@dataclass(eq=False, repr=False)
class GetModuleMetadataRequest(betterproto.Message):
    """Request for GetModuleMetadata."""

    pass


@dataclass(eq=False, repr=False)
class GetModuleMetadataResponse(betterproto.Message):
    """Response from GetModuleMetadata."""

    key: str = betterproto.string_field(1)
    description: str = betterproto.string_field(2)


@dataclass(eq=False, repr=False)
class GetFacePostSchemaRequest(betterproto.Message):
    """Request for GetFacePostSchema."""

    pass


@dataclass(eq=False, repr=False)
class GetFacePostSchemaResponse(betterproto.Message):
    """Response from GetFacePostSchema."""

    schema: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetModulePostSchemaRequest(betterproto.Message):
    """Request for GetModulePostSchema."""

    pass


@dataclass(eq=False, repr=False)
class GetModulePostSchemaResponse(betterproto.Message):
    """Response from GetModulePostSchema."""

    schema: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetControllerStatusRequest(betterproto.Message):
    """Request for GetControllerStatus."""

    pass


@dataclass(eq=False, repr=False)
class GetControllerStatusResponse(betterproto.Message):
    """Response from GetControllerStatus."""

    status: "Status" = betterproto.enum_field(1)


@dataclass(eq=False, repr=False)
class WatchControllerStatusRequest(betterproto.Message):
    """Request for WatchControllerStatus."""

    pass


@dataclass(eq=False, repr=False)
class WatchControllerStatusResponse(betterproto.Message):
    """Response from WatchControllerStatus."""

    status: "Status" = betterproto.enum_field(1)


@dataclass(eq=False, repr=False)
class GetFaceStatusRequest(betterproto.Message):
    """Request for GetFaceStatus."""

    pass


@dataclass(eq=False, repr=False)
class GetFaceStatusResponse(betterproto.Message):
    """Response from GetFaceStatus."""

    status: "Status" = betterproto.enum_field(1)


@dataclass(eq=False, repr=False)
class WatchFaceStatusRequest(betterproto.Message):
    """Request for WatchFaceStatus."""

    pass


@dataclass(eq=False, repr=False)
class WatchFaceStatusResponse(betterproto.Message):
    """Response from WatchFaceStatus."""

    status: "Status" = betterproto.enum_field(1)


@dataclass(eq=False, repr=False)
class GetModuleStatusRequest(betterproto.Message):
    """Request for GetModuleStatus."""

    pass


@dataclass(eq=False, repr=False)
class GetModuleStatusResponse(betterproto.Message):
    """Response from GetModuleStatus."""

    status: "Status" = betterproto.enum_field(1)


@dataclass(eq=False, repr=False)
class WatchModuleStatusRequest(betterproto.Message):
    """Request for WatchModuleStatus."""

    pass


@dataclass(eq=False, repr=False)
class WatchModuleStatusResponse(betterproto.Message):
    """Response from WatchModuleStatus."""

    status: "Status" = betterproto.enum_field(1)


@dataclass(eq=False, repr=False)
class GetTrainingStatusRequest(betterproto.Message):
    """Request for GetTrainingStatus."""

    pass


@dataclass(eq=False, repr=False)
class GetTrainingStatusResponse(betterproto.Message):
    """Response from GetTrainingStatus."""

    status: "TrainingStatus" = betterproto.enum_field(1)


@dataclass(eq=False, repr=False)
class WatchTrainingStatusRequest(betterproto.Message):
    """Request for WatchTrainingStatus."""

    pass


@dataclass(eq=False, repr=False)
class WatchTrainingStatusResponse(betterproto.Message):
    """Response from WatchTrainingStatus."""

    status: "TrainingStatus" = betterproto.enum_field(1)


@dataclass(eq=False, repr=False)
class GetControllerConfigSchemaRequest(betterproto.Message):
    """Request for GetControllerConfigSchema."""

    pass


@dataclass(eq=False, repr=False)
class GetControllerConfigSchemaResponse(betterproto.Message):
    """Response from GetControllerConfigSchema."""

    schema: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetControllerConfigRequest(betterproto.Message):
    """Request for GetControllerConfig."""

    pass


@dataclass(eq=False, repr=False)
class GetControllerConfigResponse(betterproto.Message):
    """Response from GetControllerConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class WatchControllerConfigRequest(betterproto.Message):
    """Request for WatchControllerConfig."""

    pass


@dataclass(eq=False, repr=False)
class WatchControllerConfigResponse(betterproto.Message):
    """Response from WatchControllerConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class SetControllerConfigRequest(betterproto.Message):
    """Request for SetControllerConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class SetControllerConfigResponse(betterproto.Message):
    """Response from SetControllerConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetFaceConfigSchemaRequest(betterproto.Message):
    """Request for GetFaceConfigSchema."""

    pass


@dataclass(eq=False, repr=False)
class GetFaceConfigSchemaResponse(betterproto.Message):
    """Response from GetFaceConfigSchema."""

    schema: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetFaceConfigRequest(betterproto.Message):
    """Request for GetFaceConfig."""

    pass


@dataclass(eq=False, repr=False)
class GetFaceConfigResponse(betterproto.Message):
    """Response from GetFaceConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class WatchFaceConfigRequest(betterproto.Message):
    """Request for WatchFaceConfig."""

    pass


@dataclass(eq=False, repr=False)
class WatchFaceConfigResponse(betterproto.Message):
    """Response from WatchFaceConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class SetFaceConfigRequest(betterproto.Message):
    """Request for SetFaceConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class SetFaceConfigResponse(betterproto.Message):
    """Response from SetFaceConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetModuleConfigSchemaRequest(betterproto.Message):
    """Request for GetModuleConfigSchema."""

    pass


@dataclass(eq=False, repr=False)
class GetModuleConfigSchemaResponse(betterproto.Message):
    """Response from GetModuleConfigSchema."""

    schema: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class GetModuleConfigRequest(betterproto.Message):
    """Request for GetModuleConfig."""

    pass


@dataclass(eq=False, repr=False)
class GetModuleConfigResponse(betterproto.Message):
    """Response from GetModuleConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class WatchModuleConfigRequest(betterproto.Message):
    """Request for WatchModuleConfig."""

    pass


@dataclass(eq=False, repr=False)
class WatchModuleConfigResponse(betterproto.Message):
    """Response from WatchModuleConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class SetModuleConfigRequest(betterproto.Message):
    """Request for SetModuleConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class SetModuleConfigResponse(betterproto.Message):
    """Response from SetModuleConfig."""

    config: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class TrainOfflineRequest(betterproto.Message):
    """Request for TrainOffline."""

    pass


@dataclass(eq=False, repr=False)
class TrainOfflineResponse(betterproto.Message):
    """Response from TrainOffline."""

    pass


@dataclass(eq=False, repr=False)
class TrainOnlineRequest(betterproto.Message):
    """Request for TrainOnline."""

    pass


@dataclass(eq=False, repr=False)
class TrainOnlineResponse(betterproto.Message):
    """Response from TrainOnline."""

    pass


@dataclass(eq=False, repr=False)
class StopTrainingRequest(betterproto.Message):
    """Request for StopTraining."""

    pass


@dataclass(eq=False, repr=False)
class StopTrainingResponse(betterproto.Message):
    """Response from StopTraining."""

    pass


@dataclass(eq=False, repr=False)
class MetricConfig(betterproto.Message):
    """Metric configuration data."""

    id: str = betterproto.string_field(1)
    label: str = betterproto.string_field(2)
    config: str = betterproto.string_field(3)
    tags: List[str] = betterproto.string_field(4)


@dataclass(eq=False, repr=False)
class GetModuleMetricsConfigRequest(betterproto.Message):
    """Request for GetModuleMetricsConfig."""

    pass


@dataclass(eq=False, repr=False)
class GetModuleMetricsConfigResponse(betterproto.Message):
    """Response from GetModuleMetricsConfig."""

    configs: List["MetricConfig"] = betterproto.message_field(1)


@dataclass(eq=False, repr=False)
class MetricData(betterproto.Message):
    """Metric data."""

    metric_id: str = betterproto.string_field(1)
    dataset_id: int = betterproto.uint64_field(2)
    data: str = betterproto.string_field(3)


@dataclass(eq=False, repr=False)
class GetModuleMetricsRequest(betterproto.Message):
    """Request for GetModuleMetrics."""

    pass


@dataclass(eq=False, repr=False)
class GetModuleMetricsResponse(betterproto.Message):
    """Response from GetModuleMetrics."""

    metrics: List["MetricData"] = betterproto.message_field(1)


@dataclass(eq=False, repr=False)
class WatchModuleMetricsRequest(betterproto.Message):
    """Request for WatchModuleMetrics."""

    pass


@dataclass(eq=False, repr=False)
class WatchModuleMetricsResponse(betterproto.Message):
    """Response from WatchModuleMetrics."""

    metric: "MetricData" = betterproto.message_field(1)


@dataclass(eq=False, repr=False)
class WatchAllRequest(betterproto.Message):
    """Request for WatchAll."""

    pass


@dataclass(eq=False, repr=False)
class WatchAllResponse(betterproto.Message):
    """Response from WatchAll."""

    method: str = betterproto.string_field(1)
    message: str = betterproto.string_field(2)


@dataclass(eq=False, repr=False)
class ResetControllerRequest(betterproto.Message):
    """Request for ResetController."""

    pass


@dataclass(eq=False, repr=False)
class ResetControllerResponse(betterproto.Message):
    """Response from ResetController."""

    pass


@dataclass(eq=False, repr=False)
class ResetFaceRequest(betterproto.Message):
    """Request for ResetFace."""

    pass


@dataclass(eq=False, repr=False)
class ResetFaceResponse(betterproto.Message):
    """Response from ResetFace."""

    pass


@dataclass(eq=False, repr=False)
class ResetModuleRequest(betterproto.Message):
    """Request for ResetModule."""

    pass


@dataclass(eq=False, repr=False)
class ResetModuleResponse(betterproto.Message):
    """Response from ResetModule."""

    pass


@dataclass(eq=False, repr=False)
class SaveControllerRequest(betterproto.Message):
    """Request for SaveController."""

    pass


@dataclass(eq=False, repr=False)
class SaveControllerResponse(betterproto.Message):
    """Response from SaveController."""

    pass


@dataclass(eq=False, repr=False)
class SaveFaceRequest(betterproto.Message):
    """Request for SaveFace."""

    pass


@dataclass(eq=False, repr=False)
class SaveFaceResponse(betterproto.Message):
    """Response from SaveFace."""

    pass


@dataclass(eq=False, repr=False)
class SaveModuleRequest(betterproto.Message):
    """Request for SaveModule."""

    pass


@dataclass(eq=False, repr=False)
class SaveModuleResponse(betterproto.Message):
    """Response from SaveModule."""

    pass


@dataclass(eq=False, repr=False)
class GetFeedRequest(betterproto.Message):
    """Request for GetFeed."""

    pass


@dataclass(eq=False, repr=False)
class GetFeedResponse(betterproto.Message):
    """Response from GetFeed."""

    id: str = betterproto.string_field(1)
    url: str = betterproto.string_field(2)
    content: str = betterproto.string_field(3)
    created_at: str = betterproto.string_field(4)


@dataclass(eq=False, repr=False)
class WatchFeedRequest(betterproto.Message):
    """Request for WatchFeed."""

    pass


@dataclass(eq=False, repr=False)
class WatchFeedResponse(betterproto.Message):
    """Response from WatchFeed."""

    id: str = betterproto.string_field(1)
    url: str = betterproto.string_field(2)
    content: str = betterproto.string_field(3)
    created_at: str = betterproto.string_field(4)


@dataclass(eq=False, repr=False)
class GeneratePostsRequest(betterproto.Message):
    """Request for GeneratePosts."""

    quantity: int = betterproto.uint64_field(1)


@dataclass(eq=False, repr=False)
class GeneratePostsResponse(betterproto.Message):
    """Response from GeneratePosts."""

    content: str = betterproto.string_field(1)
