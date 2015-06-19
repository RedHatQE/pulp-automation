import json
from tests import pulp_test
from pulp_auto.repo import Repo, Importer, Distributor
from pulp_auto.task import Task,  TaskFailure
from pulp_auto.units import Orphans
from tests.conf.roles import ROLES
from tests.conf.facade.iso import IsoRepo, IsoImporter, IsoDistributor, DEFAULT_FEED


def setUpModule():
    pass


class IsoRepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(IsoRepoTest, cls).setUpClass()
        # FIXME: hardwired role
        cls.repo_role = {
            'id': cls.__name__ + '_repo',
            'feed': DEFAULT_FEED,
            'proxy': ROLES.get('proxy'),
        }
        cls.repo = Repo(data=IsoRepo.from_role(cls.repo_role).as_data())


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
        self.repo.delta_update(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(Repo.get(self.pulp, self.repo.id).data['display_name'], display_name)

    def test_05_associate_importer(self):
        importer_facade = IsoImporter.from_role(self.repo_role)
        response = self.repo.associate_importer(self.pulp, data=importer_facade.as_data())
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)
        importer = self.repo.get_importer(self.pulp, importer_facade.id)
        self.assertEqual(
            importer,
            {
                'id': importer_facade.id,
                'importer_type_id': importer_facade.importer_type_id,
                'repo_id': self.repo.id,
                'config': importer_facade.importer_config,
                'last_sync': None
            }
        )

    def test_06_associate_distributor(self):
        distributor_facade = IsoDistributor.from_role(self.repo_role)
        response = self.repo.associate_distributor(self.pulp, data=distributor_facade.as_data())
        self.assertPulp(code=201)
        distributor = Distributor.from_response(response)
        self.assertEqual(
            distributor,
            {
                'id': distributor_facade.distributor_id,
                'distributor_type_id': distributor_facade.distributor_type_id,
                'repo_id': self.repo.id,
                'config': distributor_facade.distributor_config,
                'last_publish': None,
                'auto_publish': distributor_facade.auto_publish,
            }
        )

    def test_07_sync_repo(self):
        response = self.repo.sync(self.pulp)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_08_publish_repo(self):
        distributor_facade = IsoDistributor.from_role(self.repo_role)
        response = self.repo.publish(
            self.pulp,
            distributor_facade.distributor_id
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
