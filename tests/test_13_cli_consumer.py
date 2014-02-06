from pulp_auto.consumer import (Cli, RpmUnit, YumRepo, RpmRepo, Consumer)
from pulp_auto.task import Task
from pulp_auto.repo import create_yum_repo
from pulp_test import (PulpTest, requires_any)
from . import ROLES

def setUpModule():
    pass

def tearDownModule():
    pass

@requires_any('consumers')
@requires_any('repos', lambda repo: repo.type == 'rpm')
class CliConsumerTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        super(CliConsumerTest, cls).setUpClass()
        consumer_config = ROLES.consumers[0]
        # create all repos
        with cls.pulp.asserting(True):
            cls.repos = [create_yum_repo(cls.pulp, **repo) for repo in consumer_config.repos if repo.type == 'rpm']
            for repo, _, _ in cls.repos:
                Task.wait_for_response(cls.pulp, repo.sync(cls.pulp))
        cls.consumer_cli = Cli.ready_instance(**consumer_config)
        cls.consumer = Consumer(consumer_config)

    def test_01_api_registered_consumer(self):
        # assert the cli registration worked in API
        Consumer.get(self.pulp, self.consumer_cli.consumer_id)
        self.assertPulpOK()

    def test_02_bind_distributor(self):
        # assert binding distributor works
        # bind all repos
        with self.pulp.asserting(True):
            for repo, _, distributor in self.repos:
                binding_data = {
                    'repo_id': repo.id,
                    'distributor_id': distributor.id
                }
                Task.wait_for_response(self.pulp, self.consumer.bind_distributor(self.pulp, binding_data))

        # assert all bound repos are available on consumer
        rpm_repo_ids = set([repo.id for repo in RpmRepo.list(self.consumer_cli)])
        for repo, _, _ in self.repos:
            self.assertIn(repo.id, rpm_repo_ids)

    def test_03_unbind_repos(self):
        # assert unbinding distributors works
        with self.pulp.asserting(True):
            for repo, _, distributor in self.repos:
                Task.wait_for_response(self.pulp, self.consumer.unbind_distributor(self.pulp, repo.id, distributor.id))

    @classmethod
    def tearDownClass(cls):
        for repo, _, _ in cls.repos:
            repo.delete(cls.pulp)
        cls.consumer_cli.unregister()
        super(CliConsumerTest, cls).tearDownClass()
