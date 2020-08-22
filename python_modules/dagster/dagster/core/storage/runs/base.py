from abc import ABCMeta, abstractmethod

import six


class RunStorage(six.with_metaclass(ABCMeta)):
    """Abstract base class for storing pipeline run history.

    Note that run storages using SQL databases as backing stores should implement
    :py:class:`~dagster.core.storage.runs.SqlRunStorage`.

    Users should not directly instantiate concrete subclasses of this class; they are instantiated
    by internal machinery when ``dagit`` and ``dagster-graphql`` load, based on the values in the
    ``dagster.yaml`` file in ``$DAGSTER_HOME``. Configuration of concrete subclasses of this class
    should be done by setting values in that file.
    """

    @abstractmethod
    def add_run(self, pipeline_run):
        """Add a run to storage.

        If a run already exists with the same ID, raise DagsterRunAlreadyExists
        If the run's snapshot ID does not exist raise DagsterSnapshotDoesNotExist

        Args:
            pipeline_run (PipelineRun): The run to add.
        """

    @abstractmethod
    def handle_run_event(self, run_id, event):
        """Update run storage in accordance to a pipeline run related DagsterEvent

        Args:
            run_id (str)
            event (DagsterEvent)
        """

    @abstractmethod
    def get_runs(self, filters=None, cursor=None, limit=None):
        """Return all the runs present in the storage that match the given filters.

        Args:
            filters (Optional[PipelineRunsFilter]) -- The
                :py:class:`~dagster.core.storage.pipeline_run.PipelineRunFilter` by which to filter
                runs
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            List[PipelineRun]
        """

    @abstractmethod
    def get_runs_count(self, filters=None):
        """Return the number of runs present in the storage that match the given filters.

        Args:
            filters (Optional[PipelineRunsFilter]) -- The
                :py:class:`~dagster.core.storage.pipeline_run.PipelineRunFilter` by which to filter
                runs
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            int: The number of runs that match the given filters.
        """

    @abstractmethod
    def get_run_group(self, run_id):
        """Get the run group to which a given run belongs.

        Args:
            run_id (str): If the corresponding run is the descendant of some root run (i.e., there
                is a root_run_id on the :py:class:`PipelineRun`), that root run and all of its
                descendants are returned; otherwise, the group will consist only of the given run
                (a run that does not descend from any root is its own root).

        Returns:
            Optional[Tuple[string, List[PipelineRun]]]: If there is a corresponding run group, tuple
                whose first element is the root_run_id and whose second element is a list of all the
                descendent runs. Otherwise `None`.
        """

    @abstractmethod
    def get_run_groups(self, filters=None, cursor=None, limit=None):
        """Return all of the run groups present in the storage that include rows matching the
        given filter.

        Args:
            filter (Optional[PipelineRunsFilter]) -- The
                :py:class:`~dagster.core.storage.pipeline_run.PipelineRunFilter` by which to filter
                runs
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            Dict[Dict[Union[PipelineRun, int]]]: Specifically, a dict of the form
                ``{'pipeline_run_id': {'runs': [PipelineRun, ...], 'count': int}, ...}``. The
                instances of :py:class:`~dagster.core.pipeline_run.PipelineRun` returned in this
                data structure correspond to all of the runs that would have been returned by
                calling :py:meth:`get_run_groups` with the same arguments, plus their corresponding
                root runs, if any. The keys of this structure are the run_ids of all of the root
                runs (a run with no root is its own root). The integer counts are inclusive of all
                of the root runs' children, including those that would not have been returned by
                calling :py:meth:`get_run_groups` with the same arguments, but exclusive of the root
                run itself; i.e., if a run has no children, the count will be 0.
        """

        # Note that we could have made the opposite decision here and filtered for root runs
        # matching a given filter, etc., rather than for child runs; so that asking for the last 5
        # run groups would give the last 5 roots and their descendants, rather than the last 5
        # children and their roots. Consider the case where we have just been retrying runs
        # belonging to a group created long ago; it makes sense to bump these to the top of the
        # interface rather than burying them deeply paginated down. Note also that this query can
        # return no more run groups than there are runs in an equivalent call to get_runs, and no
        # more than 2x total instances of PipelineRun.

    @abstractmethod
    def get_run_by_id(self, run_id):
        """Get a run by its id.

        Args:
            run_id (str): The id of the run

        Returns:
            Optional[PipelineRun]
        """

    @abstractmethod
    def get_run_tags(self):
        """Get a list of tag keys and the values that have been associated with them.

        Returns:
            List[Tuple[string, Set[string]]]
        """

    @abstractmethod
    def add_run_tags(self, run_id, new_tags):
        """Add additional tags for a pipeline run.

        Args:
            run_id (str)
            new_tags (Dict[string, string])
        """

    @abstractmethod
    def has_run(self, run_id):
        """Check if the storage contains a run.

        Args:
            run_id (str): The id of the run

        Returns:
            bool
        """

    @abstractmethod
    def has_pipeline_snapshot(self, pipeline_snapshot_id):
        """Check to see if storage contains a pipeline snapshot.

        Args:
            pipeline_snapshot_id (str): The id of the run.

        Returns:
            bool
        """

    @abstractmethod
    def add_pipeline_snapshot(self, pipeline_snapshot):
        """Add a pipeline snapshot to the run store.

        Pipeline snapshots are content-addressable, meaning
        that the ID for a snapshot is a hash based on the
        body of the snapshot. This function returns
        that snapshot ID.

        Args:
            pipeline_snapshot (PipelineSnapshot)

        Return:
            str: The pipeline_snapshot_id
        """

    @abstractmethod
    def get_pipeline_snapshot(self, pipeline_snapshot_id):
        """Fetch a snapshot by ID

        Args:
            pipeline_snapshot_id (str)

        Returns:
            PipelineSnapshot
        """

    @abstractmethod
    def has_execution_plan_snapshot(self, execution_plan_snapshot_id):
        """Check to see if storage contains an execution plan snapshot.

        Args:
            execution_plan_snapshot_id (str): The id of the execution plan.

        Returns:
            bool
        """

    @abstractmethod
    def add_execution_plan_snapshot(self, execution_plan_snapshot):
        """Add an execution plan snapshot to the run store.

        Execution plan snapshots are content-addressable, meaning
        that the ID for a snapshot is a hash based on the
        body of the snapshot. This function returns
        that snapshot ID.

        Args:
            execution_plan_snapshot (ExecutionPlanSnapshot)

        Return:
            str: The execution_plan_snapshot_id
        """

    @abstractmethod
    def get_execution_plan_snapshot(self, execution_plan_snapshot_id):
        """Fetch a snapshot by ID

        Args:
            execution_plan_snapshot_id (str)

        Returns:
            ExecutionPlanSnapshot
        """

    @abstractmethod
    def wipe(self):
        """Clears the run storage."""

    @abstractmethod
    def delete_run(self, run_id):
        """Remove a run from storage"""

    def dispose(self):
        """Explicit lifecycle management."""
