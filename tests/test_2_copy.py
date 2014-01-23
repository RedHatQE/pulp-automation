import pulp_test, json, pulp_auto
from pulp_auto.repo import Repo, Importer, Distributor, create_yum_repo
from pulp_auto.task import Task, GroupTask 
 
def setUpModule():
    pass


class RepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoTest, cls).setUpClass()
        cls.repo = Repo(data={'id': cls.__name__ + "_repo"})
        cls.feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'


class SimpleRepoTest(RepoTest):

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
                'importer_type_id': 'yum_importer',
                'importer_config': {
                    'feed': self.feed
                }
            }
        )
        self.assertPulp(code=201)
        importer = Importer.from_response(response)
        importer.reload(self.pulp)
        self.assertEqual(
            importer,
            {
                'id': 'yum_importer',
                'importer_type_id': 'yum_importer',
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
        distributor.reload(self.pulp)
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

    def test_07_sync_repo(self):
        response = self.repo.sync(self.pulp)
        self.assertPulp(code=202)
        task = Task.from_response(response)[0]
        task.wait(self.pulp)

    def test_08_publish_repo(self):
        response = self.repo.publish(
            self.pulp,
            data={
                'id': 'dist_1',
                'override_config': None
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_9_copy_repo(self):

        repo_name = 'test_9'
        feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'
        source_repo = Repo(data={'id': repo_name, 'feed': feed})
        create_yum_repo(self.pulp,repo_name, feed,relative_url=repo_name)[0]
        source_repo.sync(self.pulp)
        #source_repo = Repo.get(self.pulp, self.repo.id)
        feed= None
        repo_name = 'copy'
        dest_repo = Repo(data={'id': 'copy',feed: feed})
        #dest_repo.create(self.pulp)
        dest_repo = create_yum_repo(self.pulp, repo_name, feed, relative_url=repo_name)[0]
        """dest_repo.associate_importer(self.pulp, data={
                'importer_type_id': 'yum_importer',
               'importer_config': {
                    'feed': None
                }
            })
        dest_repo.associate_distributor(self.pulp,data={
                'distributor_type_id': 'yum_distributor',
                'distributor_config': {
                    'http': False,
                    'https': True,
                        },
                'distributor_id': 'dist_1',
                'auto_publish': False
            })"""

        response = self.repo.copy(
            self.pulp,
            data={
                'source_repo_id': source_repo.id
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_10_delete_repo(self):
        self.repo.delete(self.pulp)
        self.assertPulpOK()
