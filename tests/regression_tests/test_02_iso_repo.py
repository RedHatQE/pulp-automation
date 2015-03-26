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