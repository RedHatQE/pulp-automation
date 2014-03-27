import pulp_test, json
from pulp_auto.repo import Repo, Importer, Distributor
from pulp_auto.task import Task, TaskFailure
from pulp_auto.units import Orphans


def setUpModule():
    pass


class RepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoTest, cls).setUpClass()
        cls.repo = Repo(data={'id': cls.__name__ + "_repo"})
        cls.repo2 = Repo(data={'id': cls.__name__ + "_repo2"})
        cls.feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'


class SimpleRepoTest(RepoTest):

    def test_01_create_repo(self):
        self.repo.create(self.pulp)
        self.assertPulpOK()
        #no duplicate repo
        self.repo.create(self.pulp)
        self.assertPulp(code=409)

    def test_02_get_repo(self):
        repo = Repo.get(self.pulp, self.repo.id)
        self.assertEqual(repo.id, self.repo.id)
        self.repo.reload(self.pulp)
        self.assertEqual(self.repo, repo)
        #get unexistant repo
        with self.assertRaises(AssertionError):
            Repo.get(self.pulp, 'some_id')
        self.assertPulp(code=404)

    def test_03_list_repos(self):
        repos = Repo.list(self.pulp)
        self.assertIn(self.repo, repos)

    def test_04_update_repo(self):
        display_name = 'A %s repo' % self.__class__.__name__
        self.repo |= {'display_name': display_name}
        self.repo.update(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(Repo.get(self.pulp, self.repo.id).data['display_name'], display_name)

    def test_05_list_importer(self):
        importer = self.repo.list_importers(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(importer, [])

    def test_05_list_importer_of_unexistant_repo(self):
        with self.assertRaises(AssertionError):
            self.repo2.list_importers(self.pulp)
        self.assertPulp(code=404)

    def test_06_list_distributors(self):
        distributors = self.repo.list_distributors(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(distributors, [])

    def test_06_list_distributors_of_unexistant_repo(self):
        with self.assertRaises(AssertionError):
            self.repo2.list_distributors(self.pulp)
        self.assertPulp(code=404)

    def test_07_associate_importer(self):
        response = self.repo.associate_importer(
            self.pulp,
            data={
                'importer_type_id': 'yum_importer',
                'importer_config': {
                    'feed': self.feed
                }
            }
        )
        self.assertPulp(code=202)
        importer = Repo.from_report(response)['result']
        Task.wait_for_report(self.pulp, response)
        #https://bugzilla.redhat.com/show_bug.cgi?id=1076225
        self.assertEqual({
                'id': 'yum_importer',
                'importer_type_id': 'yum_importer',
                'repo_id': self.repo.id,
                'config': {
                    'feed': self.feed
                },
                'last_sync': None
            },
            importer)

    def test_08_get_single_importer(self):
        importer=self.repo.get_importer(self.pulp, "yum_importer")
        importers = self.repo.list_importers(self.pulp)
        self.assertEqual(importer,importers[0])

    def test_09_associate_distributor(self):
        response = self.repo.associate_distributor(
            self.pulp,
            data={
                'distributor_type_id': 'yum_distributor',
                'distributor_config': {
                    'http': False,
                    'https': False,
                    'relative_url': '/zoo/'
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
                'distributor_type_id': 'yum_distributor',
                'repo_id': self.repo.id,
                'config': {
                    'http': False,
                    'https': False,
                    'relative_url': '/zoo/'
                },
                'last_publish': None,
                'auto_publish': False
            }
        )

    def test_10_get_single_distributor(self):
        distributor = self.repo.get_distributor(self.pulp, "dist_1")
        distributors = self.repo.list_distributors(self.pulp)
        self.assertIn(distributor, distributors)

    def test_11_sync_repo(self):
        response = self.repo.sync(self.pulp)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_12_publish_repo(self):
        response = self.repo.publish(
            self.pulp,
            'dist_1'
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_13_delete_repo(self):
        response = self.repo.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)
        #check you cannot delete it twice
        self.repo.delete(self.pulp)
        self.assertPulp(code=404)

    def test_14_delete_orphans(self):
        delete_response = Orphans.delete(self.pulp)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, delete_response)
