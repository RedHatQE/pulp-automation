import pulp_test, json
from pulp.repo import Repo
 
def setUpModule():
    pass


class RepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoTest, cls).setUpClass()
        cls.repo = Repo(data={'id': cls.__name__ + "_repo"})
        cls.feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'


class SimpleRepoTest(RepoTest):

    def test_01_create_repo(self):
        self.repo.create(self.pulp)
        self.assertPulpOK()

    def test_02_get_repo(self):
        repo = Repo.get(self.pulp, self.repo.id)
        self.assertEqual(repo.id, self.repo.id)
        self.repo.reload(self.pulp)
        self.assertEqual(self.repo, repo)

    def test_03_list_repos(self):
        repos = Repo.list(self.pulp)
        self.assertIn(self.repo, repos)

    def test_04_update_repo(self):
        display_name = 'A %s repo' % self.__class__.__name__
        self.repo |= {'display_name': display_name}
        self.repo.update(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(Repo.get(self.pulp, self.repo.id).data['display_name'], display_name)

    def test_05_associate_importer(self):
        self.repo.associate_importer(
            self.pulp,
            data={
                'importer_type_id': 'yum_importer',
                'importer_config': {
                    'feed': self.feed
                }
            }
        )
        self.assertPulpOK()

    def test_06_sync_repo(self):
        response = self.repo.sync(self.pulp)
        self.assertPulpOK()

    def test_07_delete_repo(self):
        self.repo.delete(self.pulp)
        self.assertPulpOK()
