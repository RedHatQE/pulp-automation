import json
from tests import pulp_test
from pulp_auto.repo import Repo
from pulp_auto.task import Task, TaskFailure
from tests.pulp_test import (ConsumerAgentPulpTest, agent_test)
from pulp_auto.consumer import (Consumer, Binding)


class DistributorBindings(ConsumerAgentPulpTest):

    @agent_test(catching=True)
    def test_01_bind_distributor(self):
        with self.pulp.asserting(True):
            response = self.consumer.bind_distributor(self.pulp, self.repo.id, self.distributor.id)
            Task.wait_for_report(self.pulp, response)

    @agent_test(catching=True)
    def test_02_update_distributor_config_via_repo_call_1078305(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1078305
        # in this custom update you can update repo's info + importer/distributor
        response = self.repo.update(self.pulp, data={
                                                   "delta": {"display_name": "NewName"},
                                                   "importer_config": {"num_units": 6},
                                                   "distributor_configs": {
                                                   self.distributor.id : {"relative_url": "my_url"}
                                                                           }
                                                    }
                                   )
        # in this case when repo is bound to a consumer the response code will be 202)
        # Seems that after fix of https://bugzilla.redhat.com/show_bug.cgi?id=1091348
        # 202 code will be returned  even when repo is not bound to the consumer, 
        # but distributor config is being updated
        self.assertPulp(code=202)
        Task.wait_for_report(self.pulp, response)

    @agent_test(catching=True)
    def test_03_delete_distributor(self):
        with self.pulp.asserting(True):
            response = self.distributor.delete(self.pulp)
            Task.wait_for_report(self.pulp, response)

    def test_04_check_binding_removed_1081030(self):
        #https://bugzilla.redhat.com/show_bug.cgi?id=1081030
        # Consumers are not unbounded from distributor in case of distributor's removal
        consumer = Consumer.get(self.pulp, self.consumer.id, params={"bindings": True})
        self.assertEqual(consumer.data["bindings"], [])
