import io
import uuid

import json
import os

import time
from collections import OrderedDict

import six

from dagster import check, seven, utils

from .scheduler import Scheduler, RunSchedule


class SystemCronScheduler(Scheduler):
    def __init__(self, schedule_dir):
        check.str_param(schedule_dir, 'schedule_dir')

        self._schedules = OrderedDict()
        self._schedule_dir = schedule_dir
        self._load_schedules()

    def create_schedule(self, *args, **kwargs):
        schedule_id = str(uuid.uuid4())
        schedule = RunSchedule(schedule_id=schedule_id, *args, **kwargs)
        self._write_schedule_to_file(schedule)
        self._schedules[schedule_id] = schedule

    def remove_schedule(self, id_):
        self._schedules.pop(id_)

    def all_schedules(self):
        return self._schedules.values()

    def all_schedules_for_pipeline(self, pipeline_name):
        return [
            s
            for s in self.all_schedules()
            if s.execution_params['selector']['name'] == pipeline_name
        ]

    def get_schedule_by_id(self, id_):
        return self._schedules.get(id_)

    def start_schedule(self, id_):
        # TODO: Create cron job and save to user's crontab
        check.not_implemented("not implemented")

    def end_schedule(self, id_):
        # TODO: Remove cron job from user's crontab
        check.not_implemented("not implmented")

    def _write_schedule_to_file(self, schedule):
        file_prefix = os.path.join(
            self._schedule_dir, '{}_{}'.format(int(time.time()), schedule.schedule_id)
        )
        metadata_file = '{}.json'.format(file_prefix)
        with io.open(metadata_file, 'w', encoding='utf-8') as f:
            json_str = seven.json.dumps(
                {
                    'schedule_id': schedule.schedule_id,
                    'name': schedule.name,
                    'cron_schedule': schedule.cron_schedule,
                    'execution_params': schedule.execution_params,
                }
            )
            f.write(six.text_type(json_str))

    def _load_schedules(self):
        utils.mkdir_p(self._schedule_dir)

        for file in os.listdir(self._schedule_dir):
            if not file.endswith('.json'):
                continue
            with open(os.path.join(self._schedule_dir, file)) as data:
                try:
                    data = json.load(data)
                    schedule = RunSchedule(
                        schedule_id=data['schedule_id'],
                        name=data['name'],
                        cron_schedule=data['cron_schedule'],
                        execution_params=data['execution_params'],
                    )

                    self._schedules[schedule.schedule_id] = schedule
                except Exception as ex:  # pylint: disable=broad-except
                    six.raise_from(
                        Exception(
                            'Could not parse dagit schedule from {file_name} in {dir_name}. {ex}: {msg}'.format(
                                file_name=file,
                                dir_name=self._schedule_dir,
                                ex=type(ex).__name__,
                                msg=ex,
                            )
                        ),
                        ex,
                    )
