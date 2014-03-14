import pulp_test, json, pulp_auto
from pulp_auto import (Request, )
from pulp_auto.repo import Repo, Importer, Distributor, Association
from pulp_auto.repo import create_puppet_repo
from pulp_auto.task import Task
from pulp_auto.units import PuppetModuleOrphan


def setUpModule():
    pass


class PuppetSearchRepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(PuppetSearchRepoTest, cls).setUpClass()
        repo_id = cls.__name__
        queries = ['tomcat']
        cls.repo, _, _ = create_puppet_repo(cls.pulp, repo_id, queries)
        cls.repo1, _, _ = create_puppet_repo(cls.pulp, repo_id + '1', queries)
        Task.wait_for_report(cls.pulp, cls.repo.sync(cls.pulp))


class SimplePuppetSearchRepoTest(PuppetSearchRepoTest):

    def test_01_search_modules_within_metadata(self):
        response = self.repo.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["puppet_module"], "filters": {"unit": {"name": "tomcat"}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        # check that filter works properly and in the result there are only modules with name 'tomcat'
        for i in range(0, len(result)):
            self.assertEqual('tomcat', result[i].data['metadata']['name'])

    def test_02_search_modules_outside_metadata(self):
        #get unit id from inside the metadata
        response = self.repo.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["puppet_module"], "filters": {"unit": {"name": "tomcat7_rhel"}}}}
        )
        self.assertPulp(code=200)
        result_old = Association.from_response(response)
        unit_id = result_old[0].data['metadata']['_id']
        # perform search outside the metadata, i.e search in the association data
        response = self.repo.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["puppet_module"], "filters": {"association": {"unit_id": unit_id}}}}
        )
        self.assertPulp(code=200)
        result_new = Association.from_response(response)
        #check that there is only one module with this id
        self.assertTrue(len(result_new) == 1)
        #check that the search inside and outside metadata is consistent
        self.assertIn(Association(data={'unit_id':unit_id}, required_data_keys=['unit_id'], relevant_data_keys=['unit_id']), result_new)

    def test_03_search_invalid_modules(self):
        response = self.repo.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["puppet_module"], "filters": {"unit": {"name": "yum"}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        self.assertTrue(result == [])

    def test_04_search_repo_in_repos(self):
        #search among puppet-repos by id
        repo = Repo.search(self.pulp, data={"criteria": {"sort": None, "fields": None, "limit": None, "filters": {"$and": [{"id": "SimplePuppetSearchRepoTest"}, {"notes._repo-type": "puppet-repo"}]}, "skip": None}})
        self.assertIn(Repo({"id": self.repo.id}, ['id'], ['id']), repo)

    def test_05_search_repo_with_regexp(self):
        #search puppet-repos with .*repo.*
        repo = Repo.search(self.pulp, data={"criteria": {"sort": None, "fields": None, "limit": None, "filters": {"$and": [{"notes._repo-type": "puppet-repo"}, {"id": {"$regex": ".*Repo.*"}}]}, "skip": None}})
        #asserting to 2 as we have two repos matched the pattern
        self.assertTrue(len(repo) == 2)

    def test_06_delete_repos(self):
        with self.pulp.async():
            self.repo.delete(self.pulp)
            self.repo1.delete(self.pulp)
        for response in list(self.pulp.last_response):
            Task.wait_for_report(self.pulp, response)

    def test_07_delete_puppet_orphans(self):
        PuppetModuleOrphan.delete_all(self.pulp)
        self.assertPulpOK()
