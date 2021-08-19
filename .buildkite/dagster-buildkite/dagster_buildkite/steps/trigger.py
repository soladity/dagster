import os
from typing import Dict, List, Optional


def trigger_step(
    pipeline: str,
    branches: Optional[List[str]] = None,
    async_step: bool = False,
    if_condition: str = None,
    env: Dict[str, str] = None,
) -> Dict:
    """trigger_step: Trigger a build of another pipeline. See:

        https://buildkite.com/docs/pipelines/trigger-step

    Parameters:
        pipeline (str): The pipeline to trigger
        branches (List[str]): List of branches to trigger
        async_step (bool): If set to true the step will immediately continue, regardless of the
            success of the triggered build. If set to false the step will wait for the triggered
            build to complete and continue only if the triggered build passed.
        if_condition (str): A boolean expression that omits the step when false. Cannot be set with
            "branches" also set.
    """
    dagster_commit_hash = os.getenv("BUILDKITE_COMMIT")
    step = {
        "trigger": pipeline,
        "label": f":link: {pipeline} from dagster@{dagster_commit_hash}",
        "async": async_step,
        "build": {
            "env": env or {},
        },
    }

    if branches:
        step["branches"] = " ".join(branches)

    if if_condition:
        step["if"] = if_condition

    return step
