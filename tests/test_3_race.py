import pulp_test, json
from pulp_test import PulpTest
from pulp_auto.repo import Repo, Importer
from pulp_auto.task import Task, GroupTask
from pulp_auto import ResponseLike, login, format_response


class RepoTest(pulp_test.PulpTest):
    def setUp(self):
        super(RepoTest, self).setUp()
        self.repo = Repo(data={'id': type(self).__name__ + "_repo"})
        self.feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'
        # assert connection works
        self.pulp.send(login.request())
        self.assertPulpOK()

    def tearDown(self):
        self.repo.delete(self.pulp)


class RaceRepoTest(RepoTest):
    def test_01_race_create_delete(self):
        with self.pulp.async():
            self.repo.create(self.pulp)
            self.repo.create(self.pulp)
        self.assertIn(ResponseLike(status_code=409), self.pulp.last_response)
        self.assertIn(ResponseLike(status_code=201), self.pulp.last_response)
