import json, pulp_auto
from tests import pulp_test
from pulp_auto.repo import Repo, Importer, Distributor, Association
from pulp_auto.task import Task
from pulp_auto.units import Orphans
from tests.conf.roles import ROLES
from tests.conf.facade.yum import YumRepo, YumImporter, YumDistributor


def setUpModule():
    pass

@pulp_test.requires_any('repos', lambda repo: repo.type == 'rpm')
class SimpleRepoCopyTest(pulp_test.PulpTest):

    @classmethod
    def setUpClass(cls):
        super(SimpleRepoCopyTest, cls).setUpClass()
        #Destination repo
        # make sure repos don't exist
        # no need to wait for repos.delete to happen
        dest_repo_name = cls.__name__ + '_copy'
        dest_repo1 = Repo({'id': dest_repo_name})
        dest_repo1.delete(cls.pulp)
        cls.dest_repo1, _, _ = YumRepo(id=dest_repo_name, importer=YumImporter(None),
                                distributors=[YumDistributor(relative_url='abc')]).create(cls.pulp)

        #2nd Destination Repo
        dest_repo_name = cls.__name__ + '_copy1'
        dest_repo2 = Repo({'id': dest_repo_name})
        dest_repo2.delete(cls.pulp)
        cls.dest_repo2, _, _ = YumRepo(id=dest_repo_name, importer=YumImporter(None),
                                distributors=[YumDistributor(relative_url='xyz')]).create(cls.pulp)

        # Source repo
        default_repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        cls.source_repo, _, _ = YumRepo.from_role(default_repo_config).create(cls.pulp)
        Task.wait_for_report(cls.pulp, cls.source_repo.sync(cls.pulp))

    def test_01_copy_repo_all(self):
        response = self.dest_repo1.copy(self.pulp, self.source_repo.id, data={})
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_02_copy_1_rpm(self):
        # copy 1 rpm
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['rpm'],
                'filters': {"unit": {"name": "cow"}}
                },
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_03_check_that_one_rpm(self):
        # check that there is precisly one module
        dest_repo2 = Repo.get(self.pulp, self.dest_repo2.id)
        self.assertEqual(dest_repo2.data['content_unit_counts']['rpm'], 1)
        # check that one exact module copied i.e. perform the search by modules name
        response = self.dest_repo2.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["rpm"], "filters": {"unit": {"name": "cow"}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        # this means that only one module found with that name
        self.assertTrue(len(result) == 1)

    def test_04_unassociate_rpm_from_copied_repo(self):
        # unassociate unit from a copied repo
        response = self.dest_repo1.unassociate_units(
            self.pulp,
            data={"criteria": {"type_ids": ["rpm"], "filters": {"unit": {"name": "cow"}}}}
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_05_check_rpm_was_unassociated(self):
        #perform a search within the repo
        response = self.dest_repo1.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["rpm"], "filters": {"unit": {"name": "cow"}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        self.assertTrue(result == [])


    def test_06_copy_rpm(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['rpm']
                },
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_07_copy_category(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['package_category']
                },
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_08_copy_group(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['package_group']
                },
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_09_copy_distribution(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['distribution']
                },
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_10_copy_erratum(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['erratum']
                },
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_11_copy_srpm(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['srpm']
                },
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    @classmethod
    def tearDownClass(cls):
        with cls.pulp.async():
            cls.source_repo.delete(cls.pulp)
            cls.dest_repo1.delete(cls.pulp)
            cls.dest_repo2.delete(cls.pulp)
        for response in list(cls.pulp.last_response):
            Task.wait_for_report(cls.pulp, response)
        #orphans also should be deleted in cleanup
        delete_response = Orphans.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, delete_response)
