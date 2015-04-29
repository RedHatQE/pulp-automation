import json, unittest
from tests import pulp_test
from pulp_auto.repo import Repo, Importer, Distributor
from pulp_auto.task import Task,  TaskFailure
from pulp_auto.units import Orphans


def setUpModule():
    pass

class DockerRepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(DockerRepoTest, cls).setUpClass()
	cls.repo = Repo(data={'id': "docker-test123"})
        cls.feed = 'https://index.docker.io/'


class SimpleDockerRepoTest(DockerRepoTest):

    def test_01_create_repo(self):
        self.repo.create(self.pulp)
        self.assertPulpOK()

    def test_02_get_repo(self):
        repo = Repo.get(self.pulp, self.repo.id)
        self.assertEqual(repo.id, self.repo.id)
        self.repo.reload(self.pulp)
        self.assertEqual(self.repo, repo)

    def test_03_list_repos(self):
        repos = Repo.list(self.pulp)
        self.assertIn(self.repo, repos)

    def test_04_update_repo(self):
        display_name = 'A %s repo' % self.__class__.__name__
        self.repo |= {'display_name': display_name}
        self.repo.delta_update(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(Repo.get(self.pulp, self.repo.id).data['display_name'], display_name)

    def test_05_associate_importer(self):
        response = self.repo.associate_importer(
            self.pulp,
            data={
                'importer_type_id': 'docker_importer',
                'importer_config': {
                    'feed': self.feed,
                     "upstream_name": "busybox"
                                     }
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)
        importer = self.repo.get_importer(self.pulp, "docker_importer")
        self.assertEqual(
            importer,
            {
                'id': 'docker_importer',
                'importer_type_id': 'docker_importer',
                'repo_id': self.repo.id,
                'config': {
                    'feed': self.feed,
                    "upstream_name": "busybox"
                },
                'last_sync': None
            }
        )

    def test_06_associate_distributor(self):
        response = self.repo.associate_distributor(
            self.pulp,
            data={
		'distributor_type_id': 'docker_distributor_web',
		'distributor_id': 'dist-1',
		'distributor_config': {
                    'http': True,
                    'https': True,
                    'relative_url': '/library/busybox'
                },
                'last_publish': None,
                'auto_publish': False
            }
        )

        self.assertPulp(code=201)
        distributor = Distributor.from_response(response)
        self.assertEqual(
            distributor,
            {
                'id': "dist-1",
                'distributor_type_id': 'docker_distributor_web',
                'repo_id': self.repo.id,
                'config': {
                    'http': True,
                    'https': True,
                    'relative_url': '/library/busybox'
                },
                'last_publish': None,
                'auto_publish': False
            }
        )

    @unittest.expectedFailure
    def test_07_sync_repo_914(self):
        # https://pulp.plan.io/issues/914
        response = self.repo.sync(self.pulp)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_08_publish_repo(self):
        response = self.repo.publish(
            self.pulp,
            'dist-1'
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_09_delete_repo(self):
        Task.wait_for_report(self.pulp, self.repo.delete(self.pulp))
        #check you cannot delete it twice
        self.repo.delete(self.pulp)
        self.assertPulp(code=404)

    def test_10_delete_orphans(self):
        delete_response = Orphans.delete(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, delete_response)
