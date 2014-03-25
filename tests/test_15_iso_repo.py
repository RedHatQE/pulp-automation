import pulp_test, json
from pulp_auto.repo import Repo, Importer, Distributor
from pulp_auto.task import Task,  TaskFailure
from pulp_auto.units import Orphans


def setUpModule():
    pass


class IsoRepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(IsoRepoTest, cls).setUpClass()
        cls.repo = Repo(data={'id': cls.__name__ + "_repo"})
        cls.feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/test_file_repo/'


class SimpleIsoRepoTest(IsoRepoTest):

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
        self.repo.update(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(Repo.get(self.pulp, self.repo.id).data['display_name'], display_name)

    def test_05_associate_importer(self):
        response = self.repo.associate_importer(
            self.pulp,
            data={
                'importer_type_id': 'iso_importer',
                'importer_config': {
                    'feed': self.feed
                }
            }
        )
        self.assertPulp(code=202)
        importer = Repo.from_report(response)['result']
        self.assertEqual(
            importer,
            {
                'id': 'iso_importer',
                'importer_type_id': 'iso_importer',
                'repo_id': self.repo.id,
                'config': {
                    'feed': self.feed
                },
                'last_sync': None
            }
        )

    def test_06_associate_distributor(self):
        response = self.repo.associate_distributor(
            self.pulp,
            data={
                'distributor_type_id': 'iso_distributor',
                'distributor_config': {
                    'http': False,
                    'https': False,
                    'relative_url': '/iso/'
                },
                'distributor_id': 'dist_1',
                'auto_publish': False
            }
        )
        self.assertPulp(code=201)
        distributor = Distributor.from_response(response)
        self.assertEqual(
            distributor,
            {
                'id': 'dist_1',
                'distributor_type_id': 'iso_distributor',
                'repo_id': self.repo.id,
                'config': {
                    'http': False,
                    'https': False,
                    'relative_url': '/iso/'
                },
                'last_publish': None,
                'auto_publish': False
            }
        )

    def test_07_sync_repo(self):
        response = self.repo.sync(self.pulp)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_08_publish_repo(self):
        response = self.repo.publish(
            self.pulp,
            'dist_1'
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
