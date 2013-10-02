import pulp_test
from pulp.repo import Repo, YumImporter
from pulp.item import ItemAssociation
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
        importer = YumImporter()
        importer.feed = 'http://ftp.linux.cz/pub/linux/fedora/linux/updates/19/x86_64/'
        # associate importer with repo and "create" the association in pulp
        self.pulp << self.repo * importer
        self.assertEqual(importer, (self.repo * importer).get(self.pulp))
        self.assertIn(importer, importer.list(self.pulp))

    def test_06_disassociate_importer(self):
        importer = YumImporter()
        importer.feed = 'http://ftp.linux.cz/pub/linux/fedora/linux/updates/19/x86_64/'
        self.pulp << self.repo / importer 
        self.assertEqual([], (self.repo * importer).list(self.pulp))

    def test_07_update_with_importer(self):
        importer = YumImporter()
        importer.feed = 'http://ftp.linux.cz/pub/linux/fedora/linux/updates/19/x86_64/'
        self.repo |= importer
        self.repo.update(self.pulp)
        self.assertPulpOK()
        # assert repo update propagates the importer
        ia = ItemAssociation(self.repo, importer)
        # GET method doesn't work with importer.id; falling-back to importer in importer.list() assert
        self.assertIn(importer, ia.list(self.pulp))
        ia.delete(self.pulp)
        self.assertPulpOK()
        # assert associating is ok with pulp
        self.repo.associate(self.pulp, importer)
        self.assertPulpOK()
        self.repo.disassociate(self.pulp, importer) 
        self.assertPulpOK()

    def test_08_delete_repo(self):
        self.repo.delete(self.pulp)
        self.assertPulpOK()
