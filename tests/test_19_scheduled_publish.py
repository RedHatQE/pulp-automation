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


class ScheduledPublishTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(ScheduledPublishTest, cls).setUpClass()
        # create and sync rpm repo
        repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        cls.repo, _, cls.distributor = create_yum_repo(cls.pulp, **repo_config)
        Task.wait_for_report(cls.pulp, cls.repo.sync(cls.pulp))
        Task.wait_for_report(cls.pulp, cls.repo.publish(cls.pulp, cls.distributor.id))
        # create a schedule publish
        cls.distributor = cls.repo.get_distributor(cls.pulp, cls.distributor.id)
        response = cls.distributor.schedule_publish(cls.pulp, "PT10M")
        cls.action = ScheduledAction.from_response(response)


class SimpleScheduledPublishTest(ScheduledPublishTest):

    def test_01_check_scheduled_publish_works(self):
        time.sleep(65)
        self.action.reload(self.pulp)
        self.assertTrue(self.action.data["total_run_count"] == 1)

    def test_02_get_scheduled_publish(self):
        schedule = self.distributor.get_scheduled_publish(self.pulp, self.action.id)
        self.assertEqual(schedule.id, self.action.id)

    def test_03_list_scheduled_publish(self):
        schedules = self.distributor.list_scheduled_publish(self.pulp)
        self.assertIn(self.action, schedules)

    def test_04_update_schedeled_publish(self):
        self.action.update(self.pulp, data={'failure_threshold': 10})
        self.assertPulpOK()
        self.action.reload(self.pulp)
        self.assertTrue(self.action.data["failure_threshold"], 10)

    def test_05_delete_scheduled_publish(self):
        self.action.delete(self.pulp)
        self.assertPulpOK()

   # def test_06_publish_history(self):
   #TODO Retrieving Publish History

    def test_06_delete_repo(self):
        response = self.repo.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)

    def test_07_delete_orphans(self):
        delete_response = Orphans.delete(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, delete_response)
