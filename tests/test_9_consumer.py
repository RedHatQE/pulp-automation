from pulp_auto.consumer import (Consumer, Binding) 
from pulp_auto.task import Task 
from pulp_test import (ConsumerAgentPulpTest, agent_test)


class TestConsumer(ConsumerAgentPulpTest):

    def test_00_none(self):
        pass

    def test_01_update_consumer(self):
        self.consumer |= {'display_name': "A %s consumer" % type(self).__name__}
        with self.pulp.asserting(True):
            self.consumer.update(self.pulp)
            self.assertEqual(Consumer.get(self.pulp, self.consumer.id), self.consumer)
    
    @agent_test(catching=True)
    def test_02_bind_distributor(self):
        with self.pulp.asserting(True):
            Task.wait_for_response(self.pulp, self.consumer.bind_distributor(self.pulp, self.binding_data))

    def test_03_get_repo_bindings(self):
        with self.pulp.asserting(True):
            bindings = self.consumer.get_repo_bindings(self.pulp, self.repo.id)
        binding = Binding(data={
            'repo_id': self.repo.id,
            'consumer_id': self.consumer.id,
            'distributor_id': self.distributor.id,
            'id': '123'
        })
        self.assertIn(binding, bindings)

    def test_04_list_bindings(self):
        with self.pulp.asserting(True):
            bindings = self.consumer.list_bindings(self.pulp)
        binding = Binding(data={
            'repo_id': self.repo.id,
            'consumer_id': self.consumer.id,
            'distributor_id': self.distributor.id,
            'id': '123'
        })
        self.assertIn(binding, bindings)

    @agent_test(catching=True)
    def test_05_unbind_distributor(self):
        with self.pulp.asserting(True):
            Task.wait_for_response(self.pulp, self.consumer.unbind_distributor(self.pulp, self.repo.id, self.distributor.id))
