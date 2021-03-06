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


class ScheduledPublishTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(ScheduledPublishTest, cls).setUpClass()
        # create and sync and publish rpm repo
        repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        cls.repo, _, [cls.distributor] = YumRepo.from_role(repo_config).create(cls.pulp)
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
        # here is tricky part,sometimes it can be 2 or 3 if last publish managed to complete by this request
        self.assertTrue(len(history) >= 2)
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
