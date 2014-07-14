import pulp_test, json
from pulp_auto.consumer_group import ConsumerGroup
from pulp_auto.common_consumer import ProtoConsumer, Binding
from pulp_auto.consumer.consumer_class import Consumer
from pulp_auto.task import Task
from pulp_test import (ConsumerAgentPulpTest, agent_test)


def setUpModule():
    pass


class ConsumerGroupContentTest(ConsumerAgentPulpTest):

    @classmethod
    def setUpClass(cls):
        super(ConsumerGroupContentTest, cls).setUpClass()
        #sync repo
        response = cls.repo.sync(cls.pulp)
        Task.wait_for_report(cls.pulp, response)
        #create consumer group
        cls.consumer_group = ConsumerGroup(data={'id': cls.__name__ + "_consumer_group"})
        cls.consumer_group.create(cls.pulp)
        with cls.agent.catching(True), cls.agent.running(cls.qpid_handle, frequency=10):
            # associate consumer to consumer group
            cls.consumer_group.associate_consumer(cls.pulp, data={"criteria": {"filters": {"id": cls.consumer.id}}})
            # bind consumer group  to the repo
            response = cls.consumer_group.bind_distributor(cls.pulp, cls.repo.id, cls.distributor.id)
            Task.wait_for_report(cls.pulp, response)
        

class SimpleConsumerGroupContentTest(ConsumerGroupContentTest):

    @agent_test(catching=True)
    def test_01_assert_unit_install(self):
        unit = {
            'name': 'pike'
        }
        response = self.consumer_group.install_unit(
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
    def test_02_assert_unit_update(self):
        unit = {
            'name': 'pike'
        }
        response = self.consumer_group.update_unit(
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
    def test_03_assert_unit_uninstall(self):
        unit = {
            'name': 'pike'
        }
        response = self.consumer_group.uninstall_unit(
                self.pulp,
                unit,
                'rpm'
            )
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    @agent_test(catching=True)
    def test_04_unbind_distributor(self):
        with self.pulp.asserting(True):
            response = self.consumer_group.unbind_distributor(self.pulp, self.repo.id, self.distributor.id)
            self.assertPulp(code=202)
            Task.wait_for_report(self.pulp, response)

    def test_05_delete_group(self):
        self.consumer_group.delete(self.pulp)
        self.assertPulpOK()

