import pulp_test, json, pulp_auto, unittest
from pulp_auto import (Request, )
from pulp_auto.repo import Repo, Importer, Distributor, Association
from pulp_auto.repo import create_puppet_repo, create_yum_repo
from pulp_auto.task import Task, TaskFailure
from pulp_auto.units import PuppetModuleOrphan, Orphans


def setUpModule():
    pass


class PuppetCopyRepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(PuppetCopyRepoTest, cls).setUpClass()
        repo_id = cls.__name__
        queries = ['tomcat']
        # create source repo and sync it to have modules fetched
        cls.source_repo, _, _ = create_puppet_repo(cls.pulp, repo_id, queries)
        Task.wait_for_report(cls.pulp, cls.source_repo.sync(cls.pulp))
        # create two destinations repos for copy purpose
        cls.dest_repo1, _, _ = create_puppet_repo(cls.pulp, repo_id + '1', feed=None)
        cls.dest_repo2, _, _ = create_puppet_repo(cls.pulp, repo_id + '2', feed=None)
        # create data for repo
        cls.invalid_repo = Repo(data={'id': cls.__name__ + "_invalidrepo"})
        # create yum repo
        cls.yumrepo, _, _ = create_yum_repo(cls.pulp, repo_id + 'yum', feed=None)


class SimplePuppetcopyRepoTest(PuppetCopyRepoTest):

    def test_01_copy_all_modules(self):
        response = self.dest_repo1.copy(self.pulp, self.source_repo.id, data={})
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_01_copy_all_modules_from_invalid_repo(self):
        response = self.dest_repo1.copy(self.pulp, "some_repo", data={})
        self.assertPulp(code=400)

    def test_01_copy_all_modules_to_invalid_repo(self):
        response = self.invalid_repo.copy(self.pulp, self.source_repo.id, data={})
        self.assertPulp(code=404)

    def test_02_check_all_modules_copied(self):
        source_repo = Repo.get(self.pulp, self.source_repo.id)
        dest_repo1 = Repo.get(self.pulp, self.dest_repo1.id)
        #check that the number of puppet modules are the same
        self.assertEqual(source_repo.data['content_unit_counts'], dest_repo1.data['content_unit_counts'])

    def test_03_copy_1_module(self):
        # attention with time this specific module can dissapear as puppetlabs are continiously upload/update/delete them
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['puppet_module'],
                'filters': {"unit": {"name": "tomcat7_rhel"}}
                },
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_03_copy_1_module_with_different_importers(self):
        # the destination repository must be configured with an importer that supports the type of units being copied.
        response = self.yumrepo.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['puppet_module'],
                'filters': {"unit": {"name": "tomcat7_rhel"}}
                },
            }
        )
        with self.assertRaises(TaskFailure):
            Task.wait_for_report(self.pulp, response)

    def test_04_check_that_one_module(self):
        # check that there is precisly one module
        dest_repo2 = Repo.get(self.pulp, self.dest_repo2.id)
        self.assertEqual(dest_repo2.data['content_unit_counts']['puppet_module'], 1)
        # check that one exact module copied i.e. perform the search by modules name
        response = self.dest_repo2.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["puppet_module"], "filters": {"unit": {"name": "tomcat7_rhel"}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        # this means that only one module found with that name
        self.assertTrue(len(result) == 1)

    @unittest.expectedFailure
    def test_05_unassociate_module_from_invalid_repo_1092417(self):
        # unassociate unit from a nonexistant repo
        # https://bugzilla.redhat.com/show_bug.cgi?id=1092417
        response = self.invalid_repo.unassociate_units(
            self.pulp,
            data={"criteria": {"type_ids": ["puppet_module"], "filters": {"unit": {"name": "tomcat7_rhel"}}}}
        )
        self.assertPulp(code=404)

    def test_05_unassociate_module_from_copied_repo_1076628(self):
        # unassociate unit from a copied repo
        # https://bugzilla.redhat.com/show_bug.cgi?id=1076628
        response = self.dest_repo1.unassociate_units(
            self.pulp,
            data={"criteria": {"type_ids": ["puppet_module"], "filters": {"unit": {"name": "tomcat7_rhel"}}}}
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_06_check_module_was_unassociated(self):
        #perform a search within the repo
        response = self.dest_repo1.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["puppet_module"], "filters": {"unit": {"name": "tomcat7_rhel"}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        self.assertTrue(result == [])

    def test_07_unassociate_module_from_repo_with_feed_1063778(self):
        # repos with feed can delete partial content inside it
        # but after next sync it will be in the initial state
        # https://bugzilla.redhat.com/show_bug.cgi?id=1063778
        response = self.source_repo.unassociate_units(
            self.pulp,
            data={"criteria": {"type_ids": ["puppet_module"], "filters": {"unit": {"name": "tomcat7_rhel"}}}}
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_08_check_module_was_unassociated(self):
        #perform a search within the repo
        response = self.source_repo.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["puppet_module"], "filters": {"unit": {"name": "tomcat7_rhel"}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        self.assertTrue(result == [])

    def test_09_check_no_orphan_appered(self):
        #check that after unassociation of module it did not appered among orphans as it is still referenced to other repo
        orphans = Orphans.get(self.pulp)
        self.assertEqual(orphans['puppet_module'], [])
        orphan_info = Orphans.info(self.pulp)
        self.assertEqual(orphan_info['puppet_module']['count'], 0)

    def test_10_check_orphan_appears(self):
        #unasosciate same module that was unassocited in dest_repo1
        response = self.dest_repo2.unassociate_units(
            self.pulp,
            data={"criteria": {"type_ids": ["puppet_module"], "filters": {"unit": {"name": "tomcat7_rhel"}}}}
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)
        #check 1 orphan appeared
        orphan_info = Orphans.info(self.pulp)
        self.assertEqual(orphan_info['puppet_module']['count'], 1)

    def test_11_repos_no_feed_cannot_be_synced(self):
        # check that repos without feed cannot be synced
        response = self.dest_repo2.sync(self.pulp)
        self.assertPulp(code=202)
        with self.assertRaises(TaskFailure):
            Task.wait_for_report(self.pulp, response)

    def test_12_delete_repos(self):
        for repo_id in [self.dest_repo1.id, self.dest_repo2.id, self.source_repo.id, self.yumrepo.id]:
            response = Repo({'id': repo_id}).delete(self.pulp)
            Task.wait_for_report(self.pulp, response)

    def test_13_delete_puppet_orphans_1109870(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1109870
        response = PuppetModuleOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_14_check_deleted_orphans(self):
        # check that all puppet_module orphans were successfully deleted
        orphans = Orphans.get(self.pulp)
        self.assertEqual(orphans['puppet_module'], [])
        orphan_info = Orphans.info(self.pulp)
        self.assertEqual(orphan_info['puppet_module']['count'], 0)
