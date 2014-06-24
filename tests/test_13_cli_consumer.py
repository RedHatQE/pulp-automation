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
        # create all repos
        # get repo configs across all consumers
        repo_configs = sum([consumer.repos for consumer in ROLES.consumers], [])
        # filter&uniq repo configs
        repo_configs = {repo.id: repo for repo in repo_configs if repo.type == 'rpm'}.values()
        with cls.pulp.asserting(True):
            cls.repos = [ create_yum_repo(cls.pulp, **repo_config) for repo_config in repo_configs ]

        # sync&publish all repos
        with cls.pulp.asserting(True):
            task_reports = [repo.sync(cls.pulp) for repo, _, _ in cls.repos]
        Task.wait_for_reports(cls.pulp, task_reports)

        with cls.pulp.asserting(True):
            task_reports = [ repo.publish(cls.pulp, distributor.id) for repo, _, distributor in cls.repos]
        Task.wait_for_reports(cls.pulp, task_reports)

        # create all consumers
        # gather all consumers
        consumer_configs = {consumer.id: consumer for consumer in ROLES.consumers}
        with cls.pulp.asserting(True):
            cls.consumers = [Consumer(consumer_config) for consumer_config in consumer_configs.values()]

        # set up consumer cli & link repos
        for consumer in cls.consumers:
            setattr(consumer, 'cli', Cli.ready_instance(**consumer_configs[consumer.id]))
            setattr(
                consumer,
                'repos',
                filter(
                    lambda (repo, importer, distributor): any(repo.id == repo_config.id for repo_config in consumer_configs[consumer.id].repos),
                    cls.repos
                )
            )

    def test_01_api_registered_consumer(self):
        # assert the cli registration worked in API
        with self.pulp.asserting(True):
            for consumer in self.consumers:
                Consumer.get(self.pulp, consumer.cli.consumer_id)

    def test_02_bind_distributor(self):
        # assert binding distributor works
        # bind all repos
        with self.pulp.asserting(True):
           task_reports = [consumer.bind_distributor(self.pulp, repo.id, distributor.id) \
                            for consumer in self.consumers for repo, _, distributor in consumer.repos]

        Task.wait_for_reports(self.pulp, task_reports)

        # assert all bound repos are available on all consumer
        for consumer in self.consumers:
            rpm_repo_ids = {repo.id for repo in RpmRepo.list(consumer.cli)}
            repo_ids = {repo.id for repo, _, _ in consumer.repos}
            self.assertEqual(repo_ids, rpm_repo_ids & repo_ids, "consumer %s misses repos: %s" % \
                (consumer, (repo_ids - (rpm_repo_ids & repo_ids))))

    def test_03_assert_yum_repos(self):
        for consumer in self.consumers:
            remote_yum_repos = YumRepo.list(consumer.cli)
            for repo, _, _ in consumer.repos:
                self.assertIn(YumRepo({'id': repo.id}), remote_yum_repos)

    def test_04_assert_unit_install(self):
        unit = {
            'name': 'zebra'
        }
        rpm = RpmUnit(unit, relevant_data_keys=unit.keys())
        with self.pulp.asserting(True):
            task_reports = [consumer.install_unit(self.pulp, unit, 'rpm') for consumer in self.consumers]
        Task.wait_for_reports(self.pulp, task_reports)

        for consumer in self.consumers:
            assert rpm in RpmUnit.list(consumer.cli), "rpm %s not installed on %s" % (rpm, consumer)

    def test_05_assert_unit_uninstall(self):
        unit = {
            'name': 'zebra'
        }
        rpm = RpmUnit(unit, relevant_data_keys=unit.keys())

        for consumer in self.consumers:
            assert rpm in RpmUnit.list(consumer.cli), "rpm %s not installed on %s" % (rpm, consumer)

        with self.pulp.asserting(True):
            task_reports = [consumer.uninstall_unit(self.pulp, unit, 'rpm') for consumer in self.consumers]
        Task.wait_for_reports(self.pulp, task_reports)

        for consumer in self.consumers:
            assert rpm not in RpmUnit.list(consumer.cli), "rpm %s still installed on %s" % (rpm, consumer)

    def test_06_assert_nonexisten_unit_install(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1062725
        # TODO parse callreport,taskreport and assert that in progress report result is false
        unit = {
            'name': '__NO_SUCH_UNIT__'
        }
        rpm = RpmUnit(unit, relevant_data_keys=unit.keys())
        with self.pulp.asserting(True):
            task_reports = [consumer.install_unit(self.pulp, unit, 'rpm') for consumer in self.consumers]
        Task.wait_for_reports(self.pulp, task_reports)

    def test_07_assert_nonexisten_unit_uninstall(self):
        unit = {
            'name': '__NO_SUCH_UNIT__'
        }
        rpm = RpmUnit(unit, relevant_data_keys=unit.keys())
        with self.pulp.asserting(True):
            task_reports = [consumer.uninstall_unit(self.pulp, unit, 'rpm') for consumer in self.consumers]
        Task.wait_for_reports(self.pulp, task_reports)

    def test_08_unbind_repos(self):
        # assert unbinding distributors works
        with self.pulp.asserting(True):
            task_reports = [consumer.unbind_distributor(self.pulp, repo.id, distributor.id) \
                            for consumer in self.consumers for repo, _, distributor in consumer.repos]
        Task.wait_for_reports(self.pulp, task_reports)

    @classmethod
    def tearDownClass(cls):
        with cls.pulp.asserting(True):
            task_reports = [repo.delete(cls.pulp) for repo, _, _ in cls.repos]
        Task.wait_for_reports(cls.pulp, task_reports)

        for consumer in cls.consumers:
            consumer.cli.unregister()
        super(CliConsumerTest, cls).tearDownClass()
