import unittest, json
from tests import pulp_test
from pulp_auto.repo import Repo, Importer, Distributor
from pulp_auto.task import Task, TaskFailure
from pulp_auto.units import Orphans


def setUpModule():
    pass


class IsoRepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(IsoRepoTest, cls).setUpClass()
        cls.repo = Repo(data={'id': cls.__name__ + "_repo",
                              "_repo-type": "iso-repo"})
        cls.repo2 = Repo(data={'id': cls.__name__ + "_repo2",
                               "_repo-type": "iso-repo"})
        cls.feed = 'https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/test_file_repo/'


class SimpleIsoRepoTest(IsoRepoTest):

    def test_01_create_repo(self):
        self.repo.create(self.pulp)
        self.assertPulpOK()
        #no duplicate repo
        self.repo.create(self.pulp)
        self.assertPulp(code=409)

    def test_02_get_repo(self):
        repo = Repo.get(self.pulp, self.repo.id)
        self.assertEqual(repo.id, self.repo.id)
        self.repo.reload(self.pulp)
        self.assertEqual(self.repo, repo)
        #get unexistant repo
        with self.assertRaises(AssertionError):
            Repo.get(self.pulp, 'some_id')
        self.assertPulp(code=404)

    def test_03_list_repos(self):
        repos = Repo.list(self.pulp)
        self.assertIn(self.repo, repos)


    #TODO FIXME not working, same as in test_02_rpm_repo.py
    def test_13_delete_repo(self):
        response = self.repo.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)
        #check you cannot delete it twice
        self.repo.delete(self.pulp)
        self.assertPulp(code=404)        