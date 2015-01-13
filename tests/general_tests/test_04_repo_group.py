import json
from tests import pulp_test
from pulp_auto.repo_group import RepoGroup
from pulp_auto.repo import Repo, Importer, Distributor
from pulp_auto.task import Task


def setUpModule():
    pass


class RepoGroupTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoGroupTest, cls).setUpClass()
        cls.repo = Repo(data={'id': cls.__name__ + "_repo"})
        cls.repo2 = Repo(data={'id': cls.__name__ + "_repo2"})
        cls.repo_group = RepoGroup(data={'id': cls.__name__ + "_repo_group"})
        cls.repo_group1 = RepoGroup(data={'id': cls.__name__ + "_repo_group1"})
        cls.repo_group2 = RepoGroup(data={'id': cls.__name__ + "_repo_group2", 'repo_ids': [cls.repo.id]})
        cls.repo_group3 = RepoGroup(data={'id': cls.__name__ + "_repo_group3", 'repo_ids': [cls.repo2.id]})
        cls.feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'


class SimpleRepoGroupTest(RepoGroupTest):

    def test_01_create_group(self):
        self.repo_group.create(self.pulp)
        self.assertPulpOK()

        # create repo
        self.repo.create(self.pulp)
        self.assertPulpOK()

    def test_02_no_dupl_repo_group(self):
        # check that you cannot create repo group with same id
        self.repo_group.create(self.pulp)
        self.assertPulp(code=409)

    def test_03_add_repo_in_creation_call(self):
        # check that you can add repo id during repo group creation call
        self.repo_group2.create(self.pulp)
        self.assertPulp(code=201)

    def test_04_add_unexistant_repo_in_creation_call_1073997(self):
        #check that you can not add unexistant repo id during repo group creation call
        #https://bugzilla.redhat.com/show_bug.cgi?id=1073997
        self.repo_group3.create(self.pulp)
        self.assertPulp(code=404)

    def test_05_update_group(self):
        display_name = 'A %s group' % self.__class__.__name__
        self.repo_group.update(self.pulp, {'display_name': display_name})
        self.assertPulp(code=200)
        self.assertEqual(RepoGroup.get(self.pulp, self.repo_group.id).data['display_name'], display_name)

    def test_06_no_repo_ids_update_group(self):
        # check you cannot update repo_ids in this call
        self.repo_group.update(self.pulp, {'repo_ids': ['another_repo']})
        self.assertPulp(code=400)
        self.assertEqual(RepoGroup.get(self.pulp, self.repo_group.id).data['repo_ids'], [])

    def test_07_update_unexistant_group(self):
        display_name = 'A %s group' % self.__class__.__name__
        self.repo_group1.update(self.pulp, {'display_name': display_name})
        self.assertPulp(code=404)

    def test_08_get_repo_group(self):
        repo_group = RepoGroup.get(self.pulp, self.repo_group.id)
        self.assertPulp(code=200)
        self.assertEqual(repo_group.id, self.repo_group.id)

    def test_09_get_unexistant_group(self):
        with self.assertRaises(AssertionError):
            RepoGroup.get(self.pulp, 'some_id')
        self.assertPulp(code=404)

    def test_10_list_repo_groups(self):
        repo_groups = RepoGroup.list(self.pulp)
        repo_group = RepoGroup.get(self.pulp, self.repo_group.id)
        self.assertPulp(code=200)
        self.assertIn(repo_group, repo_groups)

    def test_11_associate_repo(self):
        response = self.repo_group.associate_repo(self.pulp, data={"criteria": {"filters": {"id": self.repo.id}}})
        self.assertPulp(code=200)
        self.assertIn(self.repo.id, response.json())

    def test_12_associate_repo_unexistant_group(self):
        self.repo_group1.associate_repo(self.pulp, data={"criteria": {"filters": {"id": self.repo.id}}})
        self.assertPulp(code=404)

    def test_13_unassociate_repo(self):
        response = self.repo_group.unassociate_repo(self.pulp, data={"criteria": {"filters": {"id": self.repo.id}}})
        self.assertPulp(code=200)
        self.assertEqual(response.json(), [])

    def test_14_check_delete_group(self):
        self.repo_group.delete(self.pulp)
        # https://bugzilla.redhat.com/show_bug.cgi?id=1074426
        # seems that it is a doc bug only
        self.assertPulp(code=200)
        #check you cannot delete twice same repo group
        self.repo_group.delete(self.pulp)
        self.assertPulp(code=404)

    def test_15_rest_of_clean_up(self):
        self.repo_group2.delete(self.pulp)
        self.repo_group3.delete(self.pulp)
        response = self.repo.delete(self.pulp)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)
