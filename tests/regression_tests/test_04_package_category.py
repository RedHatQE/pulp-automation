from tests.pulp_test import PulpTest, requires_any, deleting
from pulp_auto.units import Orphans
from pulp_auto.repo import Repo, Importer, Distributor, Association
from pulp_auto.repo import create_yum_repo
from pulp_auto.task import (Task, TaskFailure)
from pulp_auto.upload import Upload, package_category_metadata

def setUpModule():
    pass

def tearDownModule():
    pass

class PackageCategoryTest(PulpTest):
    
    @classmethod
    def setUpClass(cls):
        super(PackageCategoryTest, cls).setUpClass()
        cls.repo1, cls.importer1, cls.distributor1 = create_yum_repo(cls.pulp, cls.__name__ + "_repo1", feed='http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/')
        cls.repo2, cls.importer2, cls.distributor2 = create_yum_repo(cls.pulp, cls.__name__ + "_repo2", feed=None)

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

        super(PackageCategoryTest, cls).tearDownClass()

    def test_01_package_category_create(self):
        response = self.repo1.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["package_group"],"limit": 1}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        groupList = []
        # make a list of names
        for i in range(0, len(result)):
            groupList.append(result[i].data['metadata']['name'])
        #create metadata for package category import
        data = package_category_metadata(self.repo1.id+"_category1", self.repo1.id, groupList)

        #actually upload category
        with deleting(self.pulp, Upload.create(self.pulp, data=data)) as upload:
            Task.wait_for_report(self.pulp, upload.import_to(self.pulp, self.repo1))
        self.assertPulp(code=200)
        
        #check that group is there and contains specified packages
        response = self.repo1.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["package_category"],\
                  "filters": {"unit": {"id": data["unit_key"]["id"]}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        self.assertEqual(result[0].data["metadata"]["packagegroupids"],
                         data["unit_metadata"]["packagegroupids"])

    def test_02_package_category_delete(self):
        groupList = []
        #create metadata for package category import        
        data = package_category_metadata(self.repo1.id+"_category1", self.repo1.id, groupList)
        #actually upload category
        with deleting(self.pulp, Upload.create(self.pulp, data=data)) as upload:
            Task.wait_for_report(self.pulp, upload.import_to(self.pulp, self.repo1))
        self.assertPulp(code=200)

        item={"criteria": {"type_ids": ["package_category"],\
                  "filters": {"unit": {"id": data["unit_key"]["id"]}}}}
        response = self.repo1.unassociate_units(self.pulp, item)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)
        #check that group is NOT there and contains specified packages
        response = self.repo1.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["package_category"],\
                  "filters": {"unit": {"id": data["unit_key"]["id"]}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        self.assertEqual(len(result), 0)        

    def test_03_package_category_copy(self):
        response = self.repo1.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["package_group"],"limit": 1}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        groupList = []
        # make a list of names
        for i in range(0, len(result)):
            groupList.append(result[i].data['metadata']['name'])
        #create metadata for package category import
        data = package_category_metadata(self.repo1.id+"_category1", self.repo1.id, groupList)
        #actually upload category
        with deleting(self.pulp, Upload.create(self.pulp, data=data)) as upload:
            Task.wait_for_report(self.pulp, upload.import_to(self.pulp, self.repo1))
        self.assertPulp(code=200)

        #copy group to other repo
        response = self.repo2.copy(
            self.pulp,
            self.repo1.id,
            data={
                'criteria': {
                'type_ids': ['package_category'],
                'filters': {"unit": {"name": data["unit_metadata"]["name"]}}
                },
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

        #check that group is there and contains specified packages
        response = self.repo2.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["package_category"],\
                  "filters": {"unit": {"id": data["unit_key"]["id"]}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        self.assertEqual(result[0].data["metadata"]["packagegroupids"],
                         data["unit_metadata"]["packagegroupids"])        