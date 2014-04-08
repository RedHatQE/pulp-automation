import pulp_test, json
from pulp_auto.repo import Repo, Importer, Distributor, create_yum_repo
from pulp_auto.task import Task, TaskFailure
from . import ROLES
from pulp_auto import path_join


def setUpModule():
    pass


class ImporterDistributorTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(ImporterDistributorTest, cls).setUpClass()
        #create repo with inporter/distributer associated
        repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        cls.repo, _, cls.distributor = create_yum_repo(cls.pulp, **repo_config)
        cls.importer = cls.repo.get_importer(cls.pulp, "yum_importer")
        cls.repo1 = Repo(data={'id': cls.__name__ + "_repo1"})

    @classmethod
    def tearDownClass(cls):
        # delete repo
        with cls.pulp.asserting(True):
            cls.repo.delete(cls.pulp)


class ImporterTest(ImporterDistributorTest):

    def test_01_list_importers(self):
        importer = self.repo.list_importers(self.pulp)
        self.assertPulp(code=200)
        self.assertIn(self.importer, importer)

    def test_02_list_importer_of_unexistant_repo(self):
        with self.assertRaises(AssertionError):
            self.repo1.list_importers(self.pulp)
            self.assertPulp(code=404)

    def test_03_get_single_importer(self):
        importer = self.repo.get_importer(self.pulp, self.importer.id)
        self.assertEqual(self.importer.id, importer.id)

    def test_04_importer_update(self):
        response = self.importer.update(self.pulp, data={"importer_config": {"num_units": 10}})
        Task.wait_for_report(self.pulp, response)
        self.importer.reload(self.pulp)
        self.assertEqual(self.importer.data["config"]["num_units"], 10)

    def test_05_importer_update_unexistent_repo(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1078833
        self.pulp.send(self.repo1.request('PUT', path=path_join(Importer.path, 'yum_importer'), data={"importer_config": {"num_units": 10}}))
        self.assertPulp(code=404)

    def test_06_delete_importer(self):
        response = self.importer.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)


class DistributorTest(ImporterDistributorTest):

    def test_01_list_distributors(self):
        distributors = self.repo.list_distributors(self.pulp)
        self.assertPulp(code=200)
        self.assertIn(self.distributor, distributors)

    def test_03_get_single_distributor(self):
        distributor = self.repo.get_distributor(self.pulp, self.distributor.id)
        self.assertEqual(self.distributor.id, distributor.id)

    def test_02_list_distributors_of_unexistant_repo(self):
        with self.assertRaises(AssertionError):
            self.repo1.list_distributors(self.pulp)
            self.assertPulp(code=404)

    def test_03_get_single_distributor(self):
        distributor = self.repo.get_distributor(self.pulp, self.distributor.id)
        self.assertEqual(self.distributor.id, distributor.id)

    def test_04_distributor_update(self):
        self.distributor.update(self.pulp, data={"distributor_config": {"relative_url": "my_url"}})
        self.distributor.reload(self.pulp)
        self.assertEqual(self.distributor.data["config"]["relative_url"], "my_url")

    def test_05_distributor_update_unexistent_repo(self):
        self.pulp.send(self.repo1.request('PUT', path=path_join(Distributor.path, 'yum_distributor'), data={"distributor_config": {"relative_url": "my_url"}}))
        self.assertPulp(code=404)

    def test_06_delete_distributor(self):
        response = self.distributor.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)
