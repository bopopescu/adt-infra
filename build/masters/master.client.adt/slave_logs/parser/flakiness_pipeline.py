# Copyright 2016 The Android Open Source Project
#
# This software is licensed under the terms of the GNU General Public
# License version 2, as published by the Free Software Foundation, and
# may be copied, distributed, and modified under those terms.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import bigquery
import bigquery_tables
import simple_parsers as sp
import site_config

import datetime
import logging
import logging.handlers
import oauth2client.client as o2cclient
import os
import os.path
import pprint
import shutil
import sys
import time


class FlakinessPipline(object):
    """A class that encapsulates the BigQuery pipeline for flakiness data."""

    TABLE_STEPS = 'steps'

    TAG_TRANSITION = 'transition'
    TAG_COMPLETE = 'complete'

    STATE_STARTED = 'started'
    STATE_JOB_SUCCESS = 'job_success'
    STATE_JOB_FAILURE = 'job_failure'
    STATE_FINISHED = 'finished'
    STATE_PIPELINE_SUCCESS = 'pipeline_success'
    STATE_PIPELINE_FAILURE = 'pipeline_failure'

    QUERY_NOW = """
    SELECT FORMAT_UTC_USEC(NOW())
    """
    QUERY_GET_STEPS = """
    SELECT
        FORMAT_UTC_USEC(timestamp) as timestamp, tag, state, job_id
    FROM
        DATASET_ID.{TABLE_STEPS} ORDER BY timestamp
    """

    def __init__(self, bigquery, bigquery_ws, workdir):
        self._bigquery = bigquery
        self._bigquery_ws = bigquery_ws
        self._workdir = workdir

    def run(self):
        self._sync_time()
        self._transition_start()
        old_steps = self._query_current_steps()
        old_tags = [x['tag'] for x in old_steps]
        if self.TAG_COMPLETE in old_tags:
            self._cleanup_workspace()
            self.run()
            return

        new_steps = []
        self._query_job_statuses(old_steps, new_steps)
        self._take_actions(old_steps, new_steps)
        self._transition_commit(new_steps)

    def _flatten(self, query):
        return query.format(
                TABLE_STEPS=self.TABLE_STEPS)

    def _sync_time(self):
        schema = [{
                'name': 'timestamp',
                'type': 'timestamp',
                'mode': 'required'
        }]
        self._remote_now = self._bigquery.sync_query(
                self._flatten(self.QUERY_NOW), schema)[0]['timestamp']
        self._local_now = datetime.datetime.utcnow()

    def _synced_now(self):
        diff = datetime.datetime.utcnow() - self._local_now
        return self._remote_now + diff

    def _transition_start(self):
        table_steps = bigquery_tables.PipelineSteps(self._workdir)
        table_steps.append_row(self._make_step_row(
                self.TAG_TRANSITION, self.STATE_STARTED))
        self._bigquery_ws.upload(table_steps, self.TABLE_STEPS)

    def _transition_commit(self, new_steps):
        table_steps = bigquery_tables.PipelineSteps(self._workdir)
        for step in new_steps:
            table_steps.append_row(step)
        table_steps.append_row(self._make_step_row(
                self.TAG_TRANSITION, self.STATE_FINISHED))
        self._bigquery_ws.upload(table_steps, self.TABLE_STEPS)

    def _query_current_steps(self):
        return self._bigquery_ws.sync_query(
                self._flatten(self.QUERY_GET_STEPS),
                bigquery_tables.PipelineSteps.SCHEMA_PATH)

    def _make_step_row(self, tag, state, job_id=None):
        return {
                'timestamp': sp.bq_format_timestamp(self._synced_now()),
                'tag': tag, 'state': state, 'job_id': job_id,
        }

    def _seal_steps(self, steps, is_good):
        if is_good:
            steps.append(self._make_step_row(
                    self.TAG_COMPLETE, self.STATE_PIPELINE_SUCCESS))
        else:
            steps.append(self._make_step_row(
                    self.TAG_COMPLETE, self.STATE_PIPELINE_FAILURE))

    def _query_job_statuses(self, old_steps, new_steps):
        job_completion_states = set([self.STATE_JOB_SUCCESS,
                                     self.STATE_JOB_FAILURE])
        started_steps = [x['tag'] for x in old_steps
                         if x['state'] == self.STATE_STARTED and
                         x['tag'] != self.TAG_TRANSITION]
        finished_steps = [x['tag'] for x in old_steps
                          if x['state'] in job_completion_states]
        outstanding_steps = set(started_steps) - set(finished_steps)
        # Get the last job_id for each outstanding job
        job_ids = {}
        for step in old_steps:
            if step['tag'] in outstanding_steps:
                job_ids[step['tag']] = step.get('job_id')

        for step in outstanding_steps:
            if job_ids[step] is None:
                logging.warning('Tag %s is outstanding, but has no job_id',
                                step)
                continue
            succeeded = False
            try:
                if not self._bigquery.job_completed(job_ids[step]):
                    continue

                succeeded = True
            except bigquery.BigQueryException:
                # Means that the step failed
                succeeded = False

            finished_step = self._make_step_row(
                    step,
                    self.STATE_JOB_SUCCESS if succeeded else
                    self.STATE_JOB_FAILURE)
            old_steps.append(finished_step)
            new_steps.append(finished_step)

    def _take_actions(self, old_steps, new_steps):
        pprint.pprint(old_steps)

        old_step_states = {}
        for step in old_steps:
            tag = step['tag']
            state = step['state']
            if tag == self.TAG_TRANSITION:
                continue
            if tag not in old_steps:
                old_step_states[tag] = set()
            old_step_states[tag].add(state)

        # Example step.
        if 'example_step' not in old_step_states:
            job_id = self._bigquery_ws.batch_query(
                    self._flatten(self.QUERY_NOW), 'ttt')
            new_steps.append(self._make_step_row('example_step',
                                                 self.STATE_STARTED,
                                                 job_id))
        elif self.STATE_FINISHED in old_step_states['example_step']:
            self._seal_steps(new_steps, True)
        elif (self.STATE_JOB_SUCCESS in old_step_states['example_step'] or
              self.STATE_JOB_FAILURE in old_step_states['example_step']):
            new_steps.append(self._make_step_row('example_step',
                                                 self.STATE_FINISHED))

    def _cleanup_workspace(self):
        logging.info('### Cleaning up workspace for a new run.')
        self._bigquery_ws.delete(self.TABLE_STEPS)


def _try_make_dir(dirname):
    try:
        os.mkdir(dirname)
    except OSError:
        # Directory exists.
        pass


def _backup_logs(workdir, backupdir):
    dst = os.path.join(backupdir,
                       'work_%s' % time.strftime('%Y%m%d-%H%M%S'))
    shutil.make_archive(dst, 'gztar', workdir, workdir)


def main(args):
    cwd = os.path.dirname(os.path.realpath(__file__))
    config = site_config.setup(cwd)

    # Any local files you write must be inside this directory.
    # Avoids polluting current directory, and allows easy backup.
    workdir = os.path.join(cwd, 'pipline_workdir')
    # Scary!
    shutil.rmtree(workdir, ignore_errors=True)
    os.mkdir(workdir)
    # In case of failure, any files created and logs are backed up here.
    backupdir = os.path.join(cwd, 'pipeline_backups')
    _try_make_dir(backupdir)
    # Otherwise, we back them up anyway, here.
    goodrunsdir = os.path.join(cwd, 'pipline_finished')
    _try_make_dir(goodrunsdir)

    log_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
    file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(workdir, 'main_log.txt'),
            maxBytes=1048576, backupCount=10)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.DEBUG)

    # Add our custom handlers to the root logger.
    logger = logging.getLogger()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)

    bq = bigquery.BigQuery(
            config[site_config.GCLOUD_PROJECT_ID],
            config[site_config.GCLOUD_BQ_DATASET_ID],
            o2cclient.GoogleCredentials.get_application_default())
    bq_ws = bigquery.BigQuery(
            config[site_config.GCLOUD_PROJECT_ID],
            config[site_config.GCLOUD_BQ_WORKSPACE_DATASET_ID],
            o2cclient.GoogleCredentials.get_application_default())

    try:
        pipeline = FlakinessPipline(bq, bq_ws, workdir)
        pipeline.run()
    except:
        # First, forcibly log the exception so that it appears in our log file.
        logging.exception('TOP LEVEL EXCEPTION')

        try:
            _backup_logs(workdir, backupdir)
        except:
            logging.warning('Backup failed after earlier error. '
                            'Failed to archive %s to %s' %
                            (workdir, backupdir))
        # Always re-raise the catch-all exception.
        raise


if __name__ == '__main__':
    main(sys.argv)
