import pulp_test, json, pulp_auto, time
from pulp_auto import (Request, ResponseLike)
from pulp_auto.repo import Repo, Importer
from pulp_auto.repo import create_yum_repo
from pulp_auto.task import Task, TaskTimeoutError
from pulp_auto.item import ScheduledAction
from pulp_auto.units import Orphans
from . import ROLES


def setUpModule():
    pass


class ScheduledPublishTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(ScheduledPublishTest, cls).setUpClass()
        # create and sync and publish rpm repo
        repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        cls.repo, _, cls.distributor = create_yum_repo(cls.pulp, **repo_config)
        Task.wait_for_report(cls.pulp, cls.repo.sync(cls.pulp))
        Task.wait_for_report(cls.pulp, cls.repo.publish(cls.pulp, cls.distributor.id))
        # create a schedule publish
        cls.distributor = cls.repo.get_distributor(cls.pulp, cls.distributor.id)
        # publish will be done every minute
        response = cls.distributor.schedule_publish(cls.pulp, "PT1M")
        cls.action = ScheduledAction.from_response(response)
        cls.delta = time.time() + 120


class SimpleScheduledPublishTest(ScheduledPublishTest):

    def test_01_check_scheduled_publish_works(self):
        while time.time() <= self.delta:
            time.sleep(1)
            self.action.reload(self.pulp)
            # total_run_count will be 2 as 'enabled' field is True by default
            # means that the scheduled sync is initially enabled
            if self.action.data["total_run_count"] == 2:
               break
        else:
            raise TaskTimeoutError('Waiting exceeded 120 second(s)', self.action.data)

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

    def test_06_publish_history(self):
        #Retrieving Publish History
        history = self.repo.get_publish_history(self.pulp, self.distributor.id)
        self.assertTrue(len(history) == 3)
        #cheking that limit filter works
        history = self.repo.get_publish_history(self.pulp, self.distributor.id, params={'limit': 1})
        self.assertTrue(len(history) == 1)

    def test_07_delete_repo(self):
        response = self.repo.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)

    def test_08_delete_orphans(self):
        delete_response = Orphans.delete(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, delete_response)
