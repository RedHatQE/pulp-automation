import pulp_test
from pulp.repo import Repo
from pulp.namespace import load_ns
 
def setUpModule():
    pass


class RepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoTest, cls).setUpClass()
        cls.repo = Repo(data=load_ns({'id': cls.__name__ + "_repo"}))


class SimpleRepoTest(RepoTest):

    def test_01_create_repo(self):
        self.repo.create(self.pulp)
        self.assertPulpOK()

    def test_02_get_repo(self):
        repo = Repo.get(self.pulp, self.repo.data.id)
        self.assertEqual(repo.data['id'], self.repo.data['id'])
        self.repo.reload(self.pulp)
        self.assertEqual(self.repo, repo)


    def test_03_list_repos(self):
        repos = Repo.list(self.pulp)
        self.assertIn(self.repo, repos)

    def test_04_delete_repo(self):
        self.repo.delete(self.pulp)
        self.assertPulpOK()
