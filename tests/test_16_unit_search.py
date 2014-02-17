import pulp_test, json, pulp_auto
from pulp_auto import (Request, ResponseLike)
from pulp_auto.repo import Repo, Importer, Distributor, Association
from pulp_auto.repo import create_puppet_repo, create_yum_repo
from pulp_auto.task import Task, GroupTask
from pulp_auto.units import Orphans, UnitFactory, AbstractUnit, PuppetModuleUnit, RpmUnit, ErratumUnit, PackageGroupUnit
from . import ROLES


def setUpModule():
    pass


class UnitSearchTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(UnitSearchTest, cls).setUpClass()
        #create and sync puppet repo
        repo_id = cls.__name__
        queries = ['tomcat']
        # make sure we run clean
        response = Repo({'id': repo_id}).delete(cls.pulp)
        if response == ResponseLike(202):
            Task.wait_for_response(cls.pulp, response)
        cls.repo1, _, _ = create_puppet_repo(cls.pulp, repo_id, queries)
        sync_task = Task.from_response(cls.repo1.sync(cls.pulp))[0]
        sync_task.wait(cls.pulp)
        # create and sync rpm repo
        repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        cls.repo2, _, _ = create_yum_repo(cls.pulp, **repo_config)
        sync_task = Task.from_response(cls.repo2.sync(cls.pulp))[0]
        sync_task.wait(cls.pulp)


class SimpleUnitSearchTest(UnitSearchTest):

    def test_01_search_puppet_units(self):
        unit = PuppetModuleUnit.search(self.pulp, data={"criteria": {"filters": {}, "fields": ["name", "_content_type_id"]}})
        # check that jenkins puppet module is present in search result
        self.assertIn(PuppetModuleUnit(data={"name": "jenkins", '_content_type_id': 'puppet_module'}, required_data_keys=['name'], relevant_data_keys=["name"]), unit)

    def test_02_search_rpm_units(self):
        unit = RpmUnit.search(self.pulp, data={"criteria": {"filters": {'name': 'zebra'}, "fields": ["name", "_content_type_id"]}, 'include_repos': True})
        self.assertIn(RpmUnit(data={"name": "zebra", '_content_type_id': 'rpm'}, required_data_keys=['name'], relevant_data_keys=["name"]), unit)
        #check that this unit is member of repo2
        self.assertIn(self.repo2.id, unit[0].data['repository_memberships'])

    def test_03_search_erratum(self):
        unit = ErratumUnit.search(self.pulp, data={"criteria": {"filters": {}, "fields": ["name", "_content_type_id"]}})
        repo2 = Repo.get(self.pulp, self.repo2.id)
        # assert that number of errata _eq_ to the number repo contains
        self.assertEqual(len(unit), repo2.data['content_unit_counts']['erratum'])

    def test_04_search_invalid_package_group(self):
        unit = PackageGroupUnit.search(self.pulp, data={"criteria": {"filters": {'_id': '111111'}, "fields": ["name", "_content_type_id"]}})
        self.assertEqual([], unit)

    def test_05_get_single_unit(self):
        #FIXME this will fail, see bz#1064934
        #retrieve unit's id
        unit_result = PuppetModuleUnit.search(self.pulp, data={"criteria": {"filters": {'name': 'jenkins'}, "fields": ["name", "_content_type_id"]}})
        unit = PuppetModuleUnit.get(self.pulp, unit_result[0].id)
        # search by unit by unit_id
        unit_result1 = PuppetModuleUnit.search(self.pulp, data={"criteria": {"filters": {'_id': unit_result[0].id}, "fields": ["name", "_content_type_id"]}})
        # assert that resuls are the same
        self.assertEqual(unit_result, unit_result1)

    def test_06_delete_repo(self):
        with self.pulp.async():
            self.repo1.delete(self.pulp)
            self.repo2.delete(self.pulp)
        for response in list(self.pulp.last_response):
            Task.wait_for_response(self.pulp, response)

    def test_07_delete_orphans(self):
        response = Orphans.delete(self.pulp)
        task = Task.from_response(response)
        task.wait(self.pulp)
