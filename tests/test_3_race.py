import pulp_test, json
from pulp_test import PulpTest
from pulp_auto.repo import Repo, create_yum_repo
from pulp_auto.task import Task
from pulp_auto import ResponseLike, login, format_response
from . import ROLES

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
        repo = Repo(data=self.repo_config)
        with self.pulp.async():
            repo.delete(self.pulp)
            repo.delete(self.pulp)
        self.assertIn(ResponseLike(status_code=404), self.pulp.last_response)
        self.assertIn(ResponseLike(status_code=202), self.pulp.last_response)
        task_responses = filter(lambda response: response == ResponseLike(status_code=202), self.pulp.last_response)
        not_responses = filter(lambda response: response == ResponseLike(status_code=404), self.pulp.last_response)
        self.assertEqual(len(task_responses), 1, "There should be just a single task response")
        for response in task_responses:
            Task.wait_for_report(self.pulp, response)

    def test_03_race_delete_published(self):
        # repos with associated importers/distributors are deleted asynchronously; a 409 may happen
        # see also: https://bugzilla.redhat.com/show_bug.cgi?id=1065455
        repo, _, distributor = create_yum_repo(self.pulp, **self.repo_config)
        repo.sync(self.pulp)
        repo.publish(self.pulp, distributor.id)
        with self.pulp.async():
            repo.delete(self.pulp)
            repo.delete(self.pulp)
        self.assertIn(ResponseLike(status_code=409), self.pulp.last_response)
        self.assertIn(ResponseLike(status_code=202), self.pulp.last_response)

        task_responses = filter(lambda response: response == ResponseLike(status_code=202), self.pulp.last_response)
        not_responses = filter(lambda response: response == ResponseLike(status_code=409), self.pulp.last_response)
        self.assertEqual(len(task_responses), 1, "There should be just a single task response")
        for response in task_responses:
            Task.wait_for_report(self.pulp, response)
