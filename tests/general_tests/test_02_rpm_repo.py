import unittest, json
from tests import pulp_test
from pulp_auto.repo import Repo, Importer, Distributor
from pulp_auto.task import Task, TaskFailure
from pulp_auto.units import Orphans
from tests.conf.facade.yum import YumRepo, YumImporter, YumDistributor
from tests.conf.roles import ROLES


def setUpModule():
    pass


class RepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoTest, cls).setUpClass()
        cls.repo = Repo(data={'id': cls.__name__ + "_repo"})
        cls.repo2 = Repo(data={'id': cls.__name__ + "_repo2"})
        cls.repo_role = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]


class SimpleRepoTest(RepoTest):

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

    def test_04_update_repo(self):
        display_name = 'A %s repo' % self.__class__.__name__
        self.repo |= {'display_name': display_name}
        self.repo.delta_update(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(Repo.get(self.pulp, self.repo.id).data['display_name'], display_name)

    def test_05_associate_importer_with_invalid_type(self):
        data = YumImporter.from_role(self.repo_role).as_data(importer_type_id='invalid_importer')
        self.repo.associate_importer(self.pulp, data=data)
        self.assertPulp(code=400)

    def test_06_associate_importer(self):
        data = YumImporter.from_role(self.repo_role).as_data()
        response = self.repo.associate_importer(self.pulp, data=data)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)
        importer = self.repo.get_importer(self.pulp, data['id'])
        # fixed as a doc bug https://bugzilla.redhat.com/show_bug.cgi?id=1076225
        self.assertEqual(importer.id, data['id'])


    def test_07_associate_importer_to_unexistant_repo(self):
        data = YumImporter.from_role(self.repo_role).as_data()
        self.repo2.associate_importer(self.pulp, data=data)
        self.assertPulp(code=404)

    def test_08_associate_distributor_with_invalid_type(self):
        data = YumDistributor.from_role(self.repo_role).as_data(
                            distributor_type_id='invalid_distributor')
        self.repo.associate_distributor(self.pulp, data=data)
        self.assertPulp(code=400)

    def test_09_associate_distributor(self):
        data = YumDistributor.from_role(self.repo_role).as_data(distributor_id='dist_1')
        response = self.repo.associate_distributor(self.pulp, data=data)
        self.assertPulp(code=201)
        distributor = Distributor.from_response(response)
        # please note although one POSTs 'distributor_id' she gets 'id' in return :-/
        self.assertEqual(data['distributor_id'], distributor.data['id'])

    def test_10_associate_distributor_to_unexistant_repo(self):
        data = YumDistributor.from_role(self.repo_role).as_data()
        self.repo2.associate_distributor(self.pulp, data)
        self.assertPulp(code=404)

    def test_11_sync_repo(self):
        response = self.repo.sync(self.pulp)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_12_publish_repo(self):
        response = self.repo.publish(
            self.pulp,
            'dist_1'
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_13_delete_repo(self):
        response = self.repo.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)
        #check you cannot delete it twice
        self.repo.delete(self.pulp)
        self.assertPulp(code=404)

    def test_14_delete_orphans(self):
        delete_response = Orphans.delete(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, delete_response)
