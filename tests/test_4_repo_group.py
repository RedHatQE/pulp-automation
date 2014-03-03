import pulp_test, json
from pulp_auto.repo_group import RepoGroup 
from pulp_auto.repo import Repo, Importer, Distributor
from pulp_auto.task import Task

def setUpModule():
    pass

class RepoGroupTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoGroupTest, cls).setUpClass()
        cls.repo_group = RepoGroup(data={'id': cls.__name__ + "_repo_group"})
        cls.repo = Repo(data={'id': cls.__name__ + "_repo"})
        cls.feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'

class SimpleRepoGroupTest(RepoGroupTest):
    
    def test_01_create_group(self):
        self.repo_group.create(self.pulp)
        self.assertPulpOK()
        
        # create repo
        self.repo.create(self.pulp)
        self.assertPulpOK()
        
    def test_02_update_group(self):
        display_name = 'A %s group' % self.__class__.__name__
        self.repo_group.update(self.pulp, {'display_name': display_name})
        self.assertPulp(code=200)
        self.assertEqual(RepoGroup.get(self.pulp, self.repo_group.id).data['display_name'], display_name)

    def test_03_get_repo_group(self):
        repo_group = RepoGroup.get(self.pulp, self.repo_group.id)
        self.assertPulp(code=200)
        self.assertEqual(repo_group.id, self.repo_group.id)
    
    def test_04_list_repo_groups(self):
        repo_groups = RepoGroup.list(self.pulp)
        repo_group = RepoGroup.get(self.pulp, self.repo_group.id)
        self.assertPulp(code=200)
        self.assertIn(repo_group, repo_groups)
 
    def test_05_associate_repo(self):
        response = self.repo_group.associate_repo(self.pulp, data={"criteria": {"filters": {"id": self.repo.id}}})
        self.assertPulp(code=200)
        self.assertIn(self.repo.id, response.json())
        
    def test_06_unassociate_repo(self):
        response = self.repo_group.unassociate_repo(self.pulp, data={"criteria": {"filters": {"id": self.repo.id}}})
        self.assertPulp(code=200)
        self.assertEqual(response.json(), [])

    def test_07_delete_group(self):
        self.repo_group.delete(self.pulp)
        self.assertPulpOK()
        
        self.repo.delete(self.pulp)
        self.assertPulpOK()

