import pulp_test
from pulp import repo
 
def setUpModule():
    pass


class RepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoTest, cls).setUpClass()
        cls.repo = repo.Repo(data={'id': cls.__name__ + "_repo"})


class SimpleRepoTest(RepoTest):

    def test_01_create_repo(self):
        self.pulp.send(self.repo.create())
        self.assertPulpOK()

    def test_02_delete_repo(self):
        self.pulp.send(self.repo.delete())
        self.assertPulpOK()
