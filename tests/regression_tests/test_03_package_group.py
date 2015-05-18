from tests.pulp_test import PulpTest, requires_any, deleting
from pulp_auto.units import Orphans
from pulp_auto.repo import Repo, Importer, Distributor, Association
from pulp_auto.repo import create_yum_repo
from pulp_auto.task import (Task, TaskFailure)
from pulp_auto.upload import Upload, package_group_metadata

def setUpModule():
    pass

def tearDownModule():
    pass

class PackageGroupTest(PulpTest):
    
    @classmethod
    def setUpClass(cls):
        super(PackageGroupTest, cls).setUpClass()
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

        super(PackageGroupTest, cls).tearDownClass()

    def test_01(self):
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
        with deleting(self.pulp, Upload.create(self.pulp, data=data)) as upload:
            Task.wait_for_report(self.pulp, upload.import_to(self.pulp, self.repo1))
        #check that group is there and contains specified packages

