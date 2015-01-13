import json
from tests import pulp_test
from pulp_auto.repo_group import RepoGroup, GroupDistributor


def setUpModule():
    pass


class DistributorGroupTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(DistributorGroupTest, cls).setUpClass()
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


class SimpleDistributorGroupTest(DistributorGroupTest):

    def test_01_associate_invalid_distributor(self):
        response = self.repo_group.associate_distributor(
                self.pulp,
                data={
                    'distributor_type_id': 'some_distributor',
                    'distributor_config': {
                        'http': False,
                        'https': False
                    },
                    'distributor_id': 'dist_2'
                }
            )
        self.assertPulp(code=400)

    def test_01_associate_distributor_to_invalid_repogroup(self):
        response = self.repo_group1.associate_distributor(
                self.pulp,
                data={
                    'distributor_type_id': 'group_export_distributor',
                    'distributor_config': {
                        'http': False,
                        'https': False
                    },
                    'distributor_id': 'dist_3'
                }
            )
        self.assertPulp(code=404)

    def test_02_get_distributor(self):
        distributor = self.repo_group.get_distributor(self.pulp, self.distributor.id)
        self.assertPulp(code=200)
        distributors = self.repo_group.list_distributors(self.pulp)
        self.assertPulp(code=200)
        self.assertIn(distributor, distributors)

    def test_02_get_non_existent_distributor(self):
        with self.assertRaises(AssertionError):
            self.repo_group.get_distributor(self.pulp, 'some_dist')
        self.assertPulp(code=404)

    def test_03_list_distributors(self):
        distributors = self.repo_group.list_distributors(self.pulp)
        self.assertPulp(code=200)

    def test_03_list_non_existent_repogroup_distributors(self):
        with self.assertRaises(AssertionError):
            self.repo_group1.list_distributors(self.pulp)
        self.assertPulp(code=404)

    def test_04_update_distributor(self):
        response = self.distributor.update(self.pulp, data={"distributor_config": {"https": True}})
        self.assertPulp(code=200)

    def test_05_delete_distributor(self):
        self.distributor.delete(self.pulp)
        self.assertPulp(code=200)

    def test_06_delete_repo_group(self):
        self.repo_group.delete(self.pulp)

    # TODO publish section when it will be documented

