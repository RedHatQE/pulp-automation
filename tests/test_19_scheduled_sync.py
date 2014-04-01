import pulp_test, json, pulp_auto, time
from pulp_auto import (Request, ResponseLike)
from pulp_auto.repo import Repo, Importer
from pulp_auto.repo import create_yum_repo
from pulp_auto.task import Task
from pulp_auto.item import ScheduledAction
from pulp_auto.units import Orphans
from . import ROLES


def setUpModule():
    pass


class ScheduledSyncTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(ScheduledSyncTest, cls).setUpClass()
        # create and sync rpm repo
        repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        cls.repo, _, _ = create_yum_repo(cls.pulp, **repo_config)
        Task.wait_for_report(cls.pulp, cls.repo.sync(cls.pulp))
        # create a schedule sync
        cls.importer = cls.repo.get_importer(cls.pulp, "yum_importer")
        response = cls.importer.schedule_sync(cls.pulp, "PT10M")
        cls.action = ScheduledAction.from_response(response)


class SimpleScheduledSyncTest(ScheduledSyncTest):

    def test_01_check_scheduled_sync_works(self):
        time.sleep(65)
        self.action.reload(self.pulp)
        self.assertTrue(self.action.data["total_run_count"] == 1)

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

   # def test_06_sync_history(self):
   #TODO Retrieving Sync History

    def test_06_delete_repo(self):
        response = self.repo.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)

    def test_07_delete_orphans(self):
        delete_response = Orphans.delete(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, delete_response)
