from tests.pulp_test import PulpTest, requires_any, deleting
from pulp_auto.units import Orphans
from pulp_auto.repo import Repo, Importer, Distributor, Association
from pulp_auto.task import (Task, TaskFailure)
from pulp_auto.upload import Upload, package_group_metadata
from tests.conf.roles import ROLES
from tests.conf.facade.yum import YumRepo, YumImporter, YumDistributor

def setUpModule():
    pass

def tearDownModule():
    pass

class PackageGroupTest(PulpTest):

    @classmethod
    def setUpClass(cls):
        super(PackageGroupTest, cls).setUpClass()
        repo_role = [repo for repo in ROLES.repos if repo.type == 'rpm'][0].copy()
        repo_role.id = cls.__name__ + '_repo1'
        cls.repo1, cls.importer1, [cls.distributor1] = YumRepo.from_role(repo_role).create(cls.pulp)
        cls.repo2, cls.importer2, [cls.distributor2] = YumRepo(id=cls.__name__ + '_repo2', importer=YumImporter(feed=None),
                    distributors=[YumDistributor(relative_url='foo')]).create(cls.pulp)

        #sync
        with cls.pulp.asserting(True):
            response = cls.repo1.sync(cls.pulp)
        Task.wait_for_report(cls.pulp, response)
        #publish
        with cls.pulp.asserting(True):
            response = cls.repo1.publish(cls.pulp, cls.distributor1.id)
        Task.wait_for_report(cls.pulp, response)

    @classmethod
    def tearDownClass(cls):
        with cls.pulp.asserting(True):
            response = cls.repo1.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, response)

        with cls.pulp.asserting(True):
            response = cls.repo2.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, response)

        # delete orphans
        with cls.pulp.asserting(True):
            response = Orphans.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, response)

        super(PackageGroupTest, cls).tearDownClass()

    def test_01_package_group_create(self):
        response = self.repo1.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["rpm"],"limit": 5}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        rpmlist = []
        # make a list of names
        for i in range(0, len(result)):
            rpmlist.append(result[i].data['metadata']['name'])
        #create metadata for package group import
        data = package_group_metadata(self.repo1.id+"_group1", self.repo1.id, rpmlist)
        #actually upload group
        with deleting(self.pulp, Upload.create(self.pulp, data=data)) as (upload,):
            Task.wait_for_report(self.pulp, upload.import_to(self.pulp, self.repo1))
        self.assertPulp(code=200)
        #check that group is there and contains specified packages
        response = self.repo1.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["package_group"],\
                  "filters": {"unit": {"id": data["unit_key"]["id"]}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        self.assertEqual(result[0].data["metadata"]["mandatory_package_names"],
                         data["unit_metadata"]["mandatory_package_names"])


    def test_02_package_group_delete(self):
        rpmlist = []
        #create metadata for package group import
        data = package_group_metadata(self.repo1.id+"_group2", self.repo1.id, rpmlist)
        #actually upload group
        with deleting(self.pulp, Upload.create(self.pulp, data=data)) as (upload,):
            Task.wait_for_report(self.pulp, upload.import_to(self.pulp, self.repo1))
        self.assertPulp(code=200)

        item={"criteria": {"type_ids": ["package_group"],\
                  "filters": {"unit": {"id": data["unit_key"]["id"]}}}}
        response = self.repo1.unassociate_units(self.pulp, item)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)
        #check that group is NOT there and contains specified packages
        response = self.repo1.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["package_group"],\
                  "filters": {"unit": {"id": data["unit_key"]["id"]}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        self.assertEqual(len(result), 0)

    def test_03_package_group_copy(self):
        response = self.repo1.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["rpm"],"limit": 5}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        rpmlist = []
        # make a list of names
        for i in range(0, len(result)):
            rpmlist.append(result[i].data['metadata']['name'])
        #create metadata for package group import
        data = package_group_metadata(self.repo1.id+"_group3", self.repo1.id, rpmlist)
        #actually upload group
        with deleting(self.pulp, Upload.create(self.pulp, data=data)) as (upload,):
            Task.wait_for_report(self.pulp, upload.import_to(self.pulp, self.repo1))
        self.assertPulp(code=200)

        #copy group to other repo
        response = self.repo2.copy(
            self.pulp,
            self.repo1.id,
            data={
                'criteria': {
                'type_ids': ['package_group'],
                'filters': {"unit": {"name": data["unit_metadata"]["name"]}}
                },
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

        #check that group is there and contains specified packages
        response = self.repo2.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["package_group"],\
                  "filters": {"unit": {"id": data["unit_key"]["id"]}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        self.assertEqual(result[0].data["metadata"]["mandatory_package_names"],
                         data["unit_metadata"]["mandatory_package_names"])
