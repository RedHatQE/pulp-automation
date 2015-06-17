import json, pulp_auto, time
from tests import pulp_test
from pulp_auto import (Request, ResponseLike)
from pulp_auto.repo import Repo, Importer
from pulp_auto.task import Task, TaskTimeoutError
from pulp_auto.item import ScheduledAction
from pulp_auto.units import Orphans
from tests.conf.roles import ROLES
from tests.conf.facade.yum import YumRepo


def setUpModule():
    pass


class ScheduledSyncTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(ScheduledSyncTest, cls).setUpClass()
        # create and sync rpm repo
        repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        cls.repo, _, _ = YumRepo.from_role(repo_config).create(cls.pulp)
        Task.wait_for_report(cls.pulp, cls.repo.sync(cls.pulp))
        # create a schedule sync
        cls.importer = cls.repo.get_importer(cls.pulp, "yum_importer")
        # sync will be done every minute
        response = cls.importer.schedule_sync(cls.pulp, "PT1M")
        cls.action = ScheduledAction.from_response(response)
        cls.delta = time.time() + 120


class SimpleScheduledSyncTest(ScheduledSyncTest):

    def test_01_check_scheduled_sync_works(self):
        while time.time() <= self.delta:
            time.sleep(1)
            self.action.reload(self.pulp)
            # total_run_count will be 2 as 'enabled' field is True by default
            # means that the scheduled sync is initially enabled
            if self.action.data["total_run_count"] == 2:
               break
        else:
            raise TaskTimeoutError('Waiting exceeded 120 second(s)', self.action.data)

    def test_02_get_scheduled_sync(self):
        schedule = self.importer.get_scheduled_sync(self.pulp, self.action.id)
        self.assertEqual(schedule.id, self.action.id)

    def test_03_list_scheduled_sync(self):
        schedules = self.importer.list_scheduled_sync(self.pulp)
        self.assertIn(self.action, schedules)

    def test_04_update_schdeuled_sync(self):
        self.action.update(self.pulp, data={'failure_threshold': 10})
        self.assertPulpOK()
        self.action.reload(self.pulp)
        self.assertTrue(self.action.data["failure_threshold"], 10)

    def test_05_delete_scheduled_sync(self):
        self.action.delete(self.pulp)
        self.assertPulpOK()

    def test_06_sync_history(self):
        # Retrieving Sync History
        history = self.repo.get_sync_history(self.pulp)
        # here is tricky part,sometimes it can be 2 or 3 if last sync managed to complete by this request
        self.assertTrue(len(history) >= 2)
        #cheking that limit filter works
        history = self.repo.get_sync_history(self.pulp, params={'limit': 1})
        self.assertTrue(len(history) == 1)

    def test_07_delete_repo(self):
        response = self.repo.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)

    def test_08_delete_orphans(self):
        delete_response = Orphans.delete(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, delete_response)
