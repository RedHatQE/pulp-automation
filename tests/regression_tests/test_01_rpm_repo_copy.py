from pulp_auto.consumer import (Cli, RpmUnit, YumRepo, RpmRepo, Consumer)
from pulp_auto.task import (Task, TaskFailure)
from pulp_auto.units import Orphans
from pulp_auto.repo import create_yum_repo, Repo, Importer, Distributor
from tests.pulp_test import (PulpTest, requires_any)
from tests import ROLES

def setUpModule():
    pass

def tearDownModule():
    pass

@requires_any('consumers')
class RegRepoCopyTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RegRepoCopyTest, cls).setUpClass()
        
        # create repo
        cls.repo1, cls.importer1, cls.distributor1 = create_yum_repo(cls.pulp, cls.__name__ + "_repo1", feed='http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/')
        cls.repo2, cls.importer2, cls.distributor2 = create_yum_repo(cls.pulp, cls.__name__ + "_repo2", feed=None)

        # create consumer
        cls.consumer = Consumer(ROLES.consumers[0])
        setattr(cls.consumer, 'cli', Cli.ready_instance(**ROLES.consumers[0]))

    def test_01_sync_repo1(self):
        with self.pulp.asserting(True):
            response = self.repo1.sync(self.pulp)
        Task.wait_for_report(self.pulp, response)
        
    def test_02_copy_repo1_to_repo2(self):
        with self.pulp.asserting(True):
            response = self.repo2.copy(self.pulp, self.repo1.id, data={})
        Task.wait_for_report(self.pulp, response)
        
        #check that the number of modules are the same
        repo1 = Repo.get(self.pulp, self.repo1.id)
        repo2 = Repo.get(self.pulp, self.repo2.id)
        self.assertEqual(repo1.data['content_unit_counts'], repo2.data['content_unit_counts'])
                      
    def test_03_publish_repo2(self):
        with self.pulp.asserting(True):        
            response = self.repo2.publish(self.pulp, self.distributor2.id)
        Task.wait_for_report(self.pulp, response)
            
    def test_04_api_registered_consumer(self):
        # assert the cli registration worked in API
        with self.pulp.asserting(True):
            Consumer.get(self.pulp, self.consumer.cli.consumer_id)

    def test_05_bind_distributor(self):
        with self.pulp.asserting(True):
           response = self.consumer.bind_distributor(self.pulp, self.repo2.id, self.distributor2.id)
        Task.wait_for_report(self.pulp, response)

    def test_06_assert_yum_repos(self):
        remote_yum_repo = YumRepo.list(self.consumer.cli)
        self.assertIn(YumRepo({'id': self.repo2.id}), remote_yum_repo)

    def test_07_assert_unit_install(self):
        unit = {
            'name': 'pike'
        }
        rpm = RpmUnit(unit, relevant_data_keys=unit.keys())
        with self.pulp.asserting(True):
            response = self.consumer.install_unit(self.pulp, unit, 'rpm')
        Task.wait_for_report(self.pulp, response)
        assert rpm in RpmUnit.list(self.consumer.cli), "rpm %s not installed on %s" % (rpm, self.consumer)

    def test_08_assert_unit_uninstall(self):
        unit = {
            'name': 'pike'
        }
        rpm = RpmUnit(unit, relevant_data_keys=unit.keys())
        assert rpm in RpmUnit.list(self.consumer.cli), "rpm %s not installed on %s" % (rpm, self.consumer)
        with self.pulp.asserting(True):
            response = self.consumer.uninstall_unit(self.pulp, unit, 'rpm')
        Task.wait_for_report(self.pulp, response)
        assert rpm not in RpmUnit.list(self.consumer.cli), "rpm %s still installed on %s" % (rpm, self.consumer)

    def test_09_unbind_repo(self):
        with self.pulp.asserting(True):
            response = self.consumer.unbind_distributor(self.pulp, self.repo2.id, self.distributor2.id)
        Task.wait_for_report(self.pulp, response)

    @classmethod
    def tearDownClass(cls):
        # delete repos
        with cls.pulp.asserting(True):
            response = cls.repo1.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, response)
        
        with cls.pulp.asserting(True):
            response = cls.repo2.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, response)
        
        # delete orphans
        with cls.pulp.asserting(True):
            response = Orphans.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, response)

        # unregister consumer
        cls.consumer.cli.unregister()
        super(RegRepoCopyTest, cls).tearDownClass()
