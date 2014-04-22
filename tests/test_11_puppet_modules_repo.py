import pulp_test, json
from pulp_auto import (Request, )
from pulp_auto.repo import Repo, Importer, Distributor
from pulp_auto.task import Task
from pulp_auto.units import PuppetModuleOrphan


def setUpModule():
    pass


class PuppetRepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(PuppetRepoTest, cls).setUpClass()
        cls.repo = Repo(data={'id': cls.__name__ + "_repo", 'notes': {"_repo-type": "puppet-repo"}})
        #modules will be fetched from puppet Forge
        cls.feed = 'http://forge.puppetlabs.com'


class SimplePuppetRepoTest(PuppetRepoTest):

    def test_01_create_repo(self):
        self.repo.create(self.pulp)
        self.assertPulpOK()

    def test_02_associate_importer(self):
        '''to the importer_config query/queries can be added to specify witch
        modules have to be synced'''
        response = self.repo.associate_importer(
            self.pulp,
            data={
                'importer_type_id': 'puppet_importer',
                'importer_config': {
                    'feed': self.feed,
                    'queries': ["stdlib", "yum"]
                }
            }
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)
        importer = self.repo.get_importer(self.pulp, "puppet_importer")
        self.assertEqual(
            importer,
            {
                'id': 'puppet_importer',
                'importer_type_id': 'puppet_importer',
                'repo_id': self.repo.id,
                'config': {
                    'feed': self.feed,
                    'queries': ["stdlib", "yum"]

                },
                'last_sync': None
            }
        )

    def test_03_associate_distributor(self):
        response = self.repo.associate_distributor(
            self.pulp,
            data={
                'distributor_type_id': 'puppet_distributor',
                'distributor_config': {
                    'http': True,
                    'https': False
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
                'distributor_type_id': 'puppet_distributor',
                'repo_id': self.repo.id,
                'config': {
                    'http': True,
                    'https': False
                },
                'last_publish': None,
                'auto_publish': False
            }
        )

    def test_04_sync_repo(self):
        '''On the initial sync, all modules (matching any queries if specified)
        will be downloaded to the Pulp server. On subsequent sync, only new
        modules and new versions of existing modules will be downloaded. Any
        modules that were once present in the feed but have been removed will
        be removed from the Pulp repository as well.'''
        response = self.repo.sync(self.pulp)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_05_publish_repo(self):
        response = self.repo.publish(
            self.pulp,
            'dist_1'
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_06_update_query_repo(self):
        #adding another query
        self.repo.update(self.pulp, data={"importer_config": {"queries": ["tomcat"]}})
        self.assertPulp(code=200)

    def test_07_sync_repo(self):
        x = Repo.get(self.pulp, self.repo.id).data['content_unit_counts']['puppet_module']
        response = self.repo.sync(self.pulp)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)
        y = Repo.get(self.pulp, self.repo.id).data['content_unit_counts']['puppet_module']
        #FIXME result can change with time as number of modules is not constant!
        #check that the second i.e. updated query was also processed.
        self.assertTrue(x != y)

    def test_08_publish_repo(self):
        response = self.repo.publish(
            self.pulp,
            'dist_1',
        )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    def test_09_delete_repo(self):
        Task.wait_for_report(self.pulp, self.repo.delete(self.pulp))

    def test_10_delete_orphans(self):
        PuppetModuleOrphan.delete_all(self.pulp)
        self.assertPulpOK()
