import json
from tests import pulp_test
from pulp_auto.task import Task
from tests.pulp_test import (ConsumerAgentPulpTest, agent_test)
from pulp_auto.consumer import (Consumer, Binding)


def setUpModule():
    pass


class BindingsRemovalTest(ConsumerAgentPulpTest):
    @classmethod
    def tearDownClass(cls):
        with \
            cls.pulp.asserting(True), \
            cls.agent.catching(False), \
            cls.agent.running(cls.qpid_handle, frequency=10)\
        :
            cls.consumer.delete(cls.pulp)
        super(ConsumerAgentPulpTest, cls).tearDownClass()


class SimpleBindingsRemovalTest(BindingsRemovalTest):

    @agent_test(catching=True)
    def test_01_bind_distributor(self):
        with self.pulp.asserting(True):
            response = self.consumer.bind_distributor(self.pulp, self.repo.id, self.distributor.id)
            Task.wait_for_report(self.pulp, response)

    def test_02_list_bindings(self):
        bindings = self.consumer.list_bindings(self.pulp)
        self.assertTrue(len(bindings) == 1)

    @agent_test(catching=True)
    def test_03_delete_repo(self):
        with self.pulp.asserting(True):
            response = self.repo.delete(self.pulp)
            Task.wait_for_report(self.pulp, response)

    def test_04_check_binding_removed_1080626(self):
        #https://bugzilla.redhat.com/show_bug.cgi?id=1080626
        # Consumers are not unbounded when repository is deleted
        consumer = Consumer.get(self.pulp, self.consumer.id, params={"bindings": True})
        self.assertEqual(consumer.data["bindings"], [])

    def test_05_list_bindings_1080642(self):
        #https://bugzilla.redhat.com/show_bug.cgi?id=1080642
        bindings = self.consumer.list_bindings(self.pulp)
        self.assertTrue(len(bindings) == 0)
