import json
from tests import pulp_test
from tests.pulp_test import PulpTest
from pulp_auto.repo import Repo, create_yum_repo
from pulp_auto.task import Task
from pulp_auto import ResponseLike, login, format_response
from .. import ROLES
from pulp_auto.task import TaskFailure

@pulp_test.requires_any('repos', lambda repo: repo.type == 'rpm')
class RaceRepoTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RaceRepoTest, cls).setUpClass()
        cls.repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        # assert connection works
        cls.pulp.send(login.request())

    @classmethod
    def tearDownClass(self):
        pass


    def test_01_race_create(self):
        repo = Repo(data=self.repo_config)
        with self.pulp.async():
            repo.create(self.pulp)
            repo.create(self.pulp)
        self.assertIn(ResponseLike(status_code=409), self.pulp.last_response)
        self.assertIn(ResponseLike(status_code=201), self.pulp.last_response)

    def test_02_race_delete(self):
        # see also: https://bugzilla.redhat.com/show_bug.cgi?id=1065455
        repo = Repo(data=self.repo_config)
        with self.pulp.async():
            repo.delete(self.pulp)
            repo.delete(self.pulp)
        responses = self.pulp.last_response
        task_reports = [report for report in responses if ResponseLike(status_code=202) == report]
        passed, failed = 0, 0
        for report in task_reports:
            try:
                Task.wait_for_report(self.pulp, report)
                passed += 1
            except TaskFailure:
                failed += 1
        if ResponseLike(status_code=404) in responses:
            self.assertEqual(passed, 1)
            self.assertEqual(failed, 0)
        else:
            self.assertEqual(passed, 1)
            self.assertEqual(failed, 1)
