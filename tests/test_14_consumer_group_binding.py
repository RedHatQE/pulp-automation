import pulp_test, json
from pulp_auto.consumer_group import ConsumerGroup
from pulp_auto.common_consumer import ProtoConsumer, Binding
from pulp_auto.consumer.consumer_class import Consumer
from pulp_auto.task import Task
from pulp_test import (ConsumerAgentPulpTest, agent_test)


def setUpModule():
    pass


class ConsumerGroupBindingTest(ConsumerAgentPulpTest):
    @classmethod
    def setUpClass(cls):
        super(ConsumerGroupBindingTest, cls).setUpClass()
        cls.consumer_group = ConsumerGroup(data={'id': cls.__name__ + "_consumer_group"})
        cls.consumer_group1 = ConsumerGroup(data={'id': cls.__name__ + "_consumer_group1", "consumer_ids":["some_consumer"]})


class SimpleConsumerGroupBindingTest(ConsumerGroupBindingTest):

    def test_01_create_group(self):
        self.consumer_group.create(self.pulp)
        self.assertPulpOK()

    @agent_test(catching=True)
    def test_02_associate_consumer(self):
        response = self.consumer_group.associate_consumer(self.pulp, data={"criteria": {"filters": {"id": self.consumer.id}}})
        self.assertPulp(code=200)
        self.assertIn(self.consumer.id, response.json())

    @agent_test(catching=True)
    def test_03_bind_non_existant_repo_bz1110668(self):
        response=self.consumer_group.bind_distributor(self.pulp, 'some-repo', self.distributor.id)
        self.assertPulp(code=400)

    @agent_test(catching=True)
    def test_03_bind_distributor(self):
        with self.pulp.asserting(True):
            response = self.consumer_group.bind_distributor(self.pulp, self.repo.id, self.distributor.id)
            self.assertPulp(code=202)
            Task.wait_for_report(self.pulp, response)

    @agent_test(catching=True)
    def test_03_bind_to_non_existant_consumer_group(self):
        response=self.consumer_group1.bind_distributor(self.pulp, self.repo.id, self.distributor.id)
        self.assertPulp(code=404)

    def test_04_check_consumer_bound(self):
        with self.pulp.asserting(True):
            single_binding = self.consumer.get_single_binding(self.pulp, self.repo.id, self.distributor.id)
        self.assertPulp(code=200)

    @agent_test(catching=True)
    def test_05_unbind_distributor(self):
        with self.pulp.asserting(True):
            response = self.consumer_group.unbind_distributor(self.pulp, self.repo.id, self.distributor.id)
            self.assertPulp(code=202)
            Task.wait_for_report(self.pulp, response)

    @agent_test(catching=True)
    def test_05_unbind_non_existant_distributor(self):
        self.consumer_group.unbind_distributor(self.pulp, self.repo.id, 'some_dist')
        self.assertPulp(code=404)

    def test_06_check_consumer_unbound(self):
        with self.assertRaises(AssertionError):
            self.consumer.get_single_binding(self.pulp, self.repo.id, self.distributor.id)
            self.assertPulp(code=404)

    def test_07_delete_group(self):
        self.consumer_group.delete(self.pulp)
        self.assertPulpOK()

