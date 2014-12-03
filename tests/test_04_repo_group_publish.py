import pulp_test, json
import unittest
from pulp_auto.repo_group import RepoGroup, GroupDistributor
from pulp_auto.task import Task
from pulp_auto.repo import create_yum_repo, Repo
from pulp_auto.units import Orphans
from . import ROLES


def setUpModule():
    pass


class PublishGroupTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(PublishGroupTest, cls).setUpClass()
        # create repo_group
        repo_group=RepoGroup(data={'id': cls.__name__ + "_repo_group"})
        response=repo_group.create(cls.pulp)
        cls.repo_group = RepoGroup.from_response(response)
        cls.repo_group1 = RepoGroup(data={'id': cls.__name__ + "_repo_group1"})

        #associate_distributor
        with cls.pulp.asserting(True):
            response = cls.repo_group.associate_distributor(
                cls.pulp,
                data={
                    'distributor_type_id': 'group_export_distributor',
                    'distributor_config': {
                        'http': False,
                        'https': False
                    },
                    'distributor_id': 'dist_1'
                }
            )
        cls.distributor = GroupDistributor.from_response(response)
        #create repo
        repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        cls.repo, _, _ = create_yum_repo(cls.pulp, **repo_config)
        Task.wait_for_report(cls.pulp, cls.repo.sync(cls.pulp))


class SimplePublishGroupTest(PublishGroupTest):


    def test_01_publish_repo_group_with_no_members_bz1148937(self):
        response = self.repo_group.publish(
            self.pulp,
            'dist_1'
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    @unittest.expectedFailure
    def test_02_publish_non_existent_repo_group_bz1148928(self):
        response = self.repo_group1.publish(
            self.pulp,
            'dist_1'
        )
        self.assertPulp(code=404)

    def test_03_associate_repo_to_repo_group(self):
        response = self.repo_group.associate_repo(self.pulp, data={"criteria": {"filters": {"id": self.repo.id}}})
        self.assertPulp(code=200)
        self.assertIn(self.repo.id, response.json())

    def test_04_publish_repo_group(self):
        response = self.repo_group.publish(
            self.pulp,
            'dist_1'
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    #TODO how to check exported iso?

    def test_05_delete_repo_group(self):
        self.repo_group.delete(self.pulp)
        self.assertPulp(code=200)

    def test_06_delete_repo(self):
        response = self.repo.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)

    def test_07_delete_orphans(self):
        delete_response = Orphans.delete(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, delete_response)

