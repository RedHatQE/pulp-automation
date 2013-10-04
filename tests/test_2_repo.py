import pulp_test
from pulp.repo import Repo
from pulp.importer import Importer, ImporterType, YUM, YUM_TYPE
from pulp.item import ItemAssociation
 
def setUpModule():
    pass


class RepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoTest, cls).setUpClass()
        cls.repo = Repo(data={'id': cls.__name__ + "_repo"})
        cls.feed = 'http://ftp.linux.cz/pub/linux/fedora/linux/updates/19/x86_64/'


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
        self.assertPulpOK()
        self.assertEqual(Repo.get(self.pulp, self.repo.id).data['display_name'], display_name)

    def test_05_associate_importer(self):
        # associate importer with repo and "create" the association in pulp
        self.pulp << self.repo * (ImporterType(YUM_TYPE) | {'importer_config': {'feed': self.feed}})
        # assert what was created in pulp equals to what was associated
        self.assertEqual(
            Importer(YUM) | {'config': {'feed': self.feed}, 'repo_id': self.repo.id},
            (self.repo * (ImporterType(YUM_TYPE) | {'importer_config': {'feed': self.feed}})).get(self.pulp)
        )

    def test_06_disassociate_importer(self):
        self.pulp << self.repo / Importer(YUM)
        self.assertEqual([], (self.repo * ImporterType(YUM_TYPE)).list(self.pulp))

    def test_07_delete_repo(self):
        self.repo.delete(self.pulp)
        self.assertPulpOK()
