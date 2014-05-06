from pulp_auto.consumer import (Cli, RpmUnit, YumRepo, RpmRepo, Consumer)
from pulp_auto.task import (Task, TaskFailure)
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
            for repo, _, distributor in cls.repos:
                Task.wait_for_report(cls.pulp, repo.sync(cls.pulp))
                Task.wait_for_report(cls.pulp, repo.publish(cls.pulp, distributor.id))
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
                Task.wait_for_report(self.pulp, self.consumer.bind_distributor(self.pulp, repo.id, distributor.id))

        # assert all bound repos are available on consumer
        rpm_repo_ids = set([repo.id for repo in RpmRepo.list(self.consumer_cli)])
        for repo, _, _ in self.repos:
            self.assertIn(repo.id, rpm_repo_ids)

    def test_03_assert_yum_repos(self):
        remote_yum_repos = YumRepo.list(self.consumer_cli)
        for repo, _, _ in self.repos:
            self.assertIn(YumRepo({'id': repo.id}), remote_yum_repos)

    def test_04_assert_unit_install(self):
        unit = {
            'name': 'zebra'
        }
        Task.wait_for_report(
            self.pulp,
            self.consumer.install_unit(
                self.pulp,
                unit,
                'rpm'
            )
        )
        self.assertIn(
            RpmUnit(unit, relevant_data_keys=unit.keys()),
            RpmUnit.list(self.consumer_cli)
        )

    def test_05_assert_unit_uninstall(self):
        unit = {
            'name': 'zebra'
        }
        self.assertIn(
            RpmUnit(unit, relevant_data_keys=unit.keys()),
            RpmUnit.list(self.consumer_cli)
        )
        Task.wait_for_report(
            self.pulp,
            self.consumer.uninstall_unit(
                self.pulp,
                unit,
                'rpm'
            )
        )
        self.assertNotIn(
            RpmUnit(unit, relevant_data_keys=unit.keys()),
            RpmUnit.list(self.consumer_cli)
        )

    def test_06_assert_nonexisten_unit_install(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1062725
        # TODO parse callreport,taskreport and assert that in progress report result is false
        unit = {
            'name': '__NO_SUCH_UNIT__'
        }
        Task.wait_for_report(
            self.pulp,
            self.consumer.install_unit(
                self.pulp,
                unit,
                'rpm'
            )
        )

    def test_07_assert_nonexisten_unit_uninstall(self):
        unit = {
            'name': '__NO_SUCH_UNIT__'
        }
        Task.wait_for_report(
            self.pulp,
            self.consumer.uninstall_unit(
                self.pulp,
                unit,
                'rpm'
            )
        )

    def test_08_unbind_repos(self):
        # assert unbinding distributors works
        with self.pulp.asserting(True):
            for repo, _, distributor in self.repos:
                Task.wait_for_report(self.pulp, self.consumer.unbind_distributor(self.pulp, repo.id, distributor.id))

    @classmethod
    def tearDownClass(cls):
        for repo, _, _ in cls.repos:
            repo.delete(cls.pulp)
        cls.consumer_cli.unregister()
        super(CliConsumerTest, cls).tearDownClass()
