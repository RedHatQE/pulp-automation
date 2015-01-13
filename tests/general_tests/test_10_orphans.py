import json, pprint, pulp_auto, unittest
from tests import pulp_test
from pulp_auto.repo import create_yum_repo, Repo
from pulp_auto.task import Task
from pulp_auto.pulp import Request
from pulp_auto import path_join
from pulp_auto.units import Orphans, UnitFactory, RpmOrphan, PackageGroupOrphan, PackageCategoryOrphan, ErratumOrphan, DistributionOrphan, DrpmOrphan, SrpmOrphan, YumRepoMetadataFileOrphan,PuppetModuleOrphan, IsoOrphan, DockerOrphan
from .. import ROLES

def setUpModule():
    pass

@pulp_test.requires_any('repos', lambda repo: repo.type == 'rpm')
class SimpleOrphanTest(pulp_test.PulpTest):

    @classmethod
    def setUpClass(cls):
        super(SimpleOrphanTest, cls).setUpClass()
        # prepare orphans by syncing and deleting a repo
        # make sure the repo is gone
        repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        repo = Repo(repo_config)
        repo.delete(cls.pulp)
        # create and sync repo
        cls.repo, _, _ = create_yum_repo(cls.pulp, **repo_config)
        Task.wait_for_report(cls.pulp, cls.repo.sync(cls.pulp))
        # this is where orphans appear
        Task.wait_for_report(cls.pulp, cls.repo.delete(cls.pulp))

    def test_00_view_all_orphaned_content(self):
        Orphans.info(self.pulp)
        self.assertPulpOK()

    def test_01_view_orphaned_content_by_type(self):
        rpm_orphans = RpmOrphan.list(self.pulp)
        self.assertPulpOK()
        all_orphans = Orphans.info(self.pulp)
        self.assertEqual(len(rpm_orphans), all_orphans['rpm']['count'])

    def test_01_view_orphaned_content_invalid_type_1092450(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1092450
        self.pulp.send(Request('GET', path_join(Orphans.path, 'invalid_type')))
        self.assertPulp(code=404)        

    def test_01_view_individual_orphan(self):
        # that does not exist
        with self.assertRaises(AssertionError):
            RpmOrphan.get(self.pulp, 'some_id')
        self.assertPulp(code=404)

    def test_01_orphan_info_data_integrity(self):
        info = Orphans.info(self.pulp)
        orphans = Orphans.get(self.pulp)
        self.assertPulpOK()
        for orphan_type_name in orphans.keys():
            # reported count info is the same as the orphans counted
            self.assertEqual(len(orphans[orphan_type_name]), info[orphan_type_name]['count'])
            orphan_type = UnitFactory.type_map.orphans[orphan_type_name]
            # '_href' is correct
            self.assertEqual(pulp_auto.path_join(pulp_auto.path, orphan_type.path), info[orphan_type_name]['_href'])
            # all orphans are of the same type
            for orphan in orphans[orphan_type_name]:
                self.assertTrue(isinstance(orphan, orphan_type), "different type: %s, %s" % (orphan_type_name, orphan.type_id))

    def test_02_delete_single_orphan(self):
        old_info = Orphans.info(self.pulp)
        rpm_orphans = RpmOrphan.list(self.pulp)
        assert rpm_orphans, "No orphans found; there might be other 'Zoo' repos in %s" % self.pulp
        response = rpm_orphans[0].delete(self.pulp)
        Task.wait_for_report(self.pulp, response)
        del rpm_orphans[0]
        self.assertPulpOK()
        new_info = Orphans.info(self.pulp)
        self.assertEqual(old_info['rpm']['count'], new_info['rpm']['count'] + 1)
        self.assertEqual(
            sorted(map(lambda x: x.data['name'], rpm_orphans)),
            sorted(map(lambda x: x.data['name'], RpmOrphan.list(self.pulp)))
        )


    def test_03_delete_orphans(self):
        delete_response = Orphans.delete(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, delete_response)
        info = Orphans.info(self.pulp)
        orphans = Orphans.get(self.pulp)
        self.assertPulpOK()
        for orphan_type_name in info.keys():
            self.assertEqual(len(orphans[orphan_type_name]), info[orphan_type_name]['count'])
            self.assertEqual(orphans[orphan_type_name], [])

    def test_04_create_orphans_again(self):
        # first a repo created, synced and then deleted
        self.setUpClass()

    # Closed Wontfix
    #def test_05_delete_orphan_by_invalid_type(self):
    #    # https://bugzilla.redhat.com/show_bug.cgi?id=1092460
    #    self.pulp.send(Request('DELETE', path_join(Orphans.path, 'invalid_type')))
    #    self.assertPulp(code=404)

    def test_05_delete_individual_orphan(self):
        rpm_orphans = RpmOrphan.list(self.pulp)
        unit_id = rpm_orphans[0]
        response = unit_id.delete(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    # Closed Wontfix
    #def test_05_delete_individual_non_exitent_orphan(self):
    #    # https://bugzilla.redhat.com/show_bug.cgi?id=1092460
    #    self.pulp.send(Request('DELETE', path_join(RpmOrphan.path, 'some_unit_id')))
    #    self.assertPulp(code=404)

    def test_06_delete_orphan_by_type_and_id_1092467(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1092467
        response = Orphans.delete_by_type_id(self.pulp, data=[{'content_type_id': 'rpm', 'unit_id': 'd0dc2044-1edc-4298-bf10-a472ea943fe1'}]
                                            )
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_07_delete_orphan_rpm_1109870(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1109870
        response = RpmOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_08_delete_orphan_pkggroup_1109870(self):
        response = PackageGroupOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_09_delete_orphan_pkgcategory_1109870(self):
        response = PackageCategoryOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_10_delete_orphan_erratum_1109870(self):
        response = ErratumOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_11_delete_orphan_distribution_1109870(self):
        response = DistributionOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_12_delete_orphan_drpm_1109870(self):
        response = DrpmOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_13_delete_orphan_srpm_1109870(self):
        response = SrpmOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_14_delete_orphan_yum_repo_metadata_1109870(self):
        response = YumRepoMetadataFileOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_15_delete_orphan_puppet_module_1109870(self):
        response = PuppetModuleOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_16_delete_orphan_ISO_1109870(self):
        response = IsoOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_17_delete_orphan_docker_1109870(self):
        response = DockerOrphan.delete_all(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    @classmethod
    def tearDownClass(cls):
        pass
