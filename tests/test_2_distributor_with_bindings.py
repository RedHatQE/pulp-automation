import pulp_test, json
from pulp_auto.repo import Repo
from pulp_auto.task import Task, TaskFailure
from pulp_test import (ConsumerAgentPulpTest, agent_test)
from pulp_auto.consumer import (Consumer, Binding)


class DistributorBindings(ConsumerAgentPulpTest):

    @agent_test(catching=True)
    def test_01_bind_distributor(self):
        with self.pulp.asserting(True):
            response = self.consumer.bind_distributor(self.pulp, self.repo.id, self.distributor.id)
            Task.wait_for_report(self.pulp, response)

    def test_02_delete_distributor(self):
        response = self.distributor.delete(self.pulp)
        Task.wait_for_report(self.pulp, response)

    def test_03_check_binding_removed(self):
        #https://bugzilla.redhat.com/show_bug.cgi?id=1081030
        # Consumers are not unbounded from distributor in case of distributor's removal
        consumer = Consumer.get(self.pulp, self.consumer.id, params={"bindings": True})
        self.assertTrue(consumer.data["bindings"] is None)
