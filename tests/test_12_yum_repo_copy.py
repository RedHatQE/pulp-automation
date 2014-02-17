import pulp_test, json, pulp_auto
from pulp_auto.repo import Repo, Importer, Distributor, create_yum_repo
from pulp_auto.task import Task, GroupTask
from pulp_auto.units import Orphans
from . import ROLES


def setUpModule():
    pass

@pulp_test.requires_any('repos', lambda repo: repo.type == 'rpm')
class SimpleRepoCopyTest(pulp_test.PulpTest):

    @classmethod
    def setUpClass(cls):
        super(SimpleRepoCopyTest, cls).setUpClass()
        #Destination repo
        # make sure repos don't exist
        # no need to wait for repos.delete to happen
        feed = None
        dest_repo_name = cls.__name__ + '_copy'
        dest_repo1 = Repo({'id': dest_repo_name})
        dest_repo1.delete(cls.pulp)
        cls.dest_repo1, _, _ = create_yum_repo(cls.pulp, dest_repo_name, feed)

        #2nd Destination Repo
        dest_repo_name = cls.__name__ + '_copy1'
        dest_repo2 = Repo({'id': dest_repo_name})
        dest_repo2.delete(cls.pulp)
        cls.dest_repo2, _, _ = create_yum_repo(cls.pulp, dest_repo_name, feed)

        # Source repo
        default_repo_config = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        source_repo_name = cls.__name__ + '_repo'
        source_repo = Repo({'id': source_repo_name})
        source_repo.delete(cls.pulp)
        cls.source_repo, _, _ = create_yum_repo(cls.pulp, source_repo_name, default_repo_config.feed)
        sync_task = Task.from_response(cls.source_repo.sync(cls.pulp))[0]
        sync_task.wait(cls.pulp)

    def test_1_copy_repo_all(self):
        response = self.dest_repo1.copy(self.pulp, self.source_repo.id, data={})
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_2_copy_rpm(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['rpm']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_3_copy_category(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['package_category']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_4_copy_group(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['package_group']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_4_copy_distribution(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['distribution']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_5_copy_erratum(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['erratum']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_6_copy_srpm(self):
        response = self.dest_repo2.copy(
            self.pulp,
            self.source_repo.id,
            data={
                'criteria': {
                'type_ids': ['srpm']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    @classmethod
    def tearDownClass(cls):
        with cls.pulp.async():
            for repo_id in ['SimpleRepoCopyTest_repo', 'SimpleRepoCopyTest_copy', 'SimpleRepoCopyTest_copy1']:
                Repo({'id': repo_id}).delete(cls.pulp)
        for response in list(cls.pulp.last_response):
            Task.wait_for_response(cls.pulp, response)
        #orphans also should be deleted in cleanup
        delete_response = Orphans.delete(cls.pulp)
        delete_task = Task.from_response(delete_response)
        delete_task.wait(cls.pulp)
