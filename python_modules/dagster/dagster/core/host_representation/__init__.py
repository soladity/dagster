'''
This subpackage contains all classes that host processes (e.g. dagit)
use to manipulate and represent definitions that are resident
in user processes and containers.  e.g. ExternalPipeline

It also contains classes that represent historical representations
that have been persisted. e.g. HistoricalPipeline
'''
from .external import (
    ExternalExecutionPlan,
    ExternalPartitionSet,
    ExternalPipeline,
    ExternalRepository,
    ExternalSchedule,
)
from .external_data import (
    ExternalPartitionData,
    ExternalPartitionSetData,
    ExternalPipelineData,
    ExternalPipelineSubsetResult,
    ExternalPresetData,
    ExternalRepositoryData,
    ExternalScheduleData,
    ExternalScheduleExecutionData,
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from .handle import (
    InProcessRepositoryLocationHandle,
    PipelineHandle,
    PythonEnvRepositoryLocationHandle,
    RepositoryHandle,
    RepositoryLocationHandle,
)
from .historical import HistoricalPipeline
from .pipeline_index import PipelineIndex
from .repository_location import (
    InProcessRepositoryLocation,
    PythonEnvRepositoryLocation,
    RepositoryLocation,
)
from .represented import RepresentedPipeline
from .selector import PipelineSelector, RepositorySelector, ScheduleSelector
