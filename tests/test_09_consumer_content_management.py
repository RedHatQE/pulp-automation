from pulp_auto.consumer.consumer_class import (Consumer, Binding, Event)
from pulp_auto.task import Task
from pulp_test import (ConsumerAgentPulpTest, agent_test)


class TestConsumer(ConsumerAgentPulpTest):

    def test_00_sync_repo(self):
        response = self.repo.sync(self.pulp)
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    @agent_test(catching=True)
    def test_01_bind_distributor(self):
        with self.pulp.asserting(True):
            response = self.consumer.bind_distributor(self.pulp, self.repo.id, self.distributor.id)
            self.assertPulp(code=202)
            Task.wait_for_report(self.pulp, response)

    @agent_test(catching=True)
    def test_02_assert_unit_install(self):
        unit = {
            'name': 'pike'
        }
        response = self.consumer.install_unit(
                self.pulp,
                unit,
                'rpm',
                options = {
                "apply": True,
                "reboot": False,
                "importkeys": False
                }

            )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)


    @agent_test(catching=True)
    def test_03_assert_unit_update(self):
        unit = {
            'name': 'pike'
        }
        response = self.consumer.update_unit(
                self.pulp,
                unit,
                'rpm',
                options = {
                "apply": True,
                "reboot": False,
                "importkeys": False
                }

            )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    @agent_test(catching=True)
    def test_04_assert_unit_uninstall(self):
        unit = {
            'name': 'pike'
        }
        response = self.consumer.uninstall_unit(
                self.pulp,
                unit,
                'rpm'
            )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    @agent_test(catching=True)
    def test_05_unbind_distributor(self):
        with self.pulp.asserting(True):
            response = self.consumer.unbind_distributor(self.pulp, self.repo.id, self.distributor.id)
            self.assertPulp(code=202)
            Task.wait_for_report(self.pulp, response)

