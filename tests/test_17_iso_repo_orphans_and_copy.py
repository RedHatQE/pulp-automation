import pulp_test, json, pulp_auto, unittest
from pulp_auto import (Request, )
from pulp_auto.repo import Repo, Importer, Distributor, Association
from pulp_auto.repo import create_iso_repo
from pulp_auto.task import Task, TaskFailure
from pulp_auto.units import IsoOrphan, Orphans


def setUpModule():
    pass


class IsoCopyRepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(IsoCopyRepoTest, cls).setUpClass()
        repo_id = cls.__name__
        feed='http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/test_file_repo/'
        # create source repo and sync it to have modules fetched
        cls.source_repo, _, _ = create_iso_repo(cls.pulp, repo_id,feed)
        Task.wait_for_report(cls.pulp, cls.source_repo.sync(cls.pulp))
        # create two destinations repos for copy purpose
        cls.dest_repo1, _, _ = create_iso_repo(cls.pulp, repo_id + '1', feed=None)
        cls.dest_repo2, _, _ = create_iso_repo(cls.pulp, repo_id + '2', feed=None)


class SimpleIsocopyRepoTest(IsoCopyRepoTest):

    def test_01_copy_all_iso(self):
        response = self.dest_repo1.copy(self.pulp, self.source_repo.id, data={})
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_02_check_all_iso_copied(self):
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
                'type_ids': ['iso'],
                'filters': {"unit": {"name": "test.iso"}}
                },
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_04_check_that_one_iso(self):
        # check that there is precisly one module
        dest_repo2 = Repo.get(self.pulp, self.dest_repo2.id)
        self.assertEqual(dest_repo2.data['content_unit_counts']['iso'], 1)
        # check that one exact module copied i.e. perform the search by modules name
        response = self.dest_repo2.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["iso"], "filters": {"unit": {"name": "test.iso"}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        # this means that only one module found with that name
        self.assertTrue(len(result) == 1)

    def test_05_unassociate_iso_from_copied_repo(self):
        # unassociate unit from a copied repo
        response = self.dest_repo1.unassociate_units(
            self.pulp,
            data={"criteria": {"type_ids": ["iso"], "filters": {"unit": {"name": "test.iso"}}}}
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_06_check_iso_was_unassociated(self):
        #perform a search within the repo
        response = self.dest_repo1.within_repo_search(
            self.pulp,
            data={"criteria": {"type_ids": ["iso"], "filters": {"unit": {"name": "test.iso"}}}}
        )
        self.assertPulp(code=200)
        result = Association.from_response(response)
        self.assertTrue(result == [])

    def test_07_no_unassociation_within_repo_with_feed(self):
        # repos with feed now can delete partial content inside it
        response = self.source_repo.unassociate_units(
            self.pulp,
            data={"criteria": {"type_ids": ["iso"], "filters": {"unit": {"name": "test.iso"}}}}
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_08_check_no_orphan_appeared(self):
        #check that after unassociation of module it did not appered among orphans as it is still referenced to other repo
        orphans = Orphans.get(self.pulp)
        self.assertEqual(orphans['iso'], [])
        orphan_info = Orphans.info(self.pulp)
        self.assertEqual(orphan_info['iso']['count'], 0)

    def test_09_check_orphan_appears(self):
        #delete source repo
        self.source_repo.delete(self.pulp)
        self.assertPulpOK()
        #unasosciate same module that was unassocited in dest_repo1
        response = self.dest_repo2.unassociate_units(
            self.pulp,
            data={"criteria": {"type_ids": ["iso"], "filters": {"unit": {"name": "test.iso"}}}}
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)
        #check 1 orphan appeared
        orphan_info = Orphans.info(self.pulp)
        self.assertEqual(orphan_info['iso']['count'], 1)

    def test_10_repos_no_feed_cannot_be_synced(self):
        # check that repos without feed cannot be synced
        response = self.dest_repo2.sync(self.pulp)
        self.assertPulp(code=202)
        with self.assertRaises(TaskFailure):
            with self.pulp.asserting(True):
                Task.wait_for_report(self.pulp, response)

    def test_11_delete_repos(self):
        response = self.dest_repo1.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)
        response = self.dest_repo2.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)

    #@unittest.expectedFailure
    def test_12_delete_iso_orphans_1109870_planned_for_next_release241(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1109870
        #response = IsoOrphan.delete_all(self.pulp)
        response = Orphans.delete(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_13_check_deleted_orphans(self):
        # check that all puppet_module orphans were successfully deleted
        orphans = Orphans.get(self.pulp)
        self.assertEqual(orphans['iso'], [])
        orphan_info = Orphans.info(self.pulp)
        self.assertEqual(orphan_info['iso']['count'], 0)
