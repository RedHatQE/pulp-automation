from pulp_auto.consumer.consumer_class import (Consumer, Binding, Event)
from pulp_auto.task import Task
from pulp_test import (ConsumerAgentPulpTest, agent_test)


class TestConsumer1080462(ConsumerAgentPulpTest):


    @agent_test(catching=True)
    def test_01_bind_distributor(self):
    # https://bugzilla.redhat.com/show_bug.cgi?id=1080462
    # "An unhandled exception is raised when notify_agent set to false in consumer bind to the repo call"
        with self.pulp.asserting(True):
            response = self.consumer.bind_distributor(self.pulp, self.repo.id, self.distributor.id, notify_agent=False)
            self.assertPulp(code=200)

    def test_02_get_repo_bindings(self):
        with self.pulp.asserting(True):
            bindings = self.consumer.get_repo_bindings(self.pulp, self.repo.id)
        binding = Binding(data={
            'repo_id': self.repo.id,
            'consumer_id': self.consumer.id,
            'distributor_id': self.distributor.id,
            'id': '123'
        })
        self.assertIn(binding, bindings)

    def test_03_list_bindings(self):
        bindings = self.consumer.list_bindings(self.pulp)
        self.assertTrue(len(bindings) == 1)

    def test_04_check_binding_present(self):
        consumer = Consumer.get(self.pulp, self.consumer.id, params={"bindings": True})
        self.assertTrue(consumer.data["bindings"] != [])



