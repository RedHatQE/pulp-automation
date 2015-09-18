from pulp_auto.consumer.consumer_class import (Consumer, Binding, Event)
from pulp_auto.task import Task, TaskTimeoutError
from tests.pulp_test import (ConsumerAgentPulpTest, agent_test)
from pulp_auto.item import  ScheduledAction
import time, unittest


class ConsumerScheduledUpdate(ConsumerAgentPulpTest):

    @classmethod
    def setUpClass(cls):
        super(ConsumerScheduledUpdate, cls).setUpClass()
        #sync repo
        response = cls.repo.sync(cls.pulp)
        Task.wait_for_report(cls.pulp, response)
        with cls.agent.catching(True), cls.agent.running(cls.qpid_handle, frequency=10):
            # bind consumer to the repo
            response = cls.consumer.bind_distributor(cls.pulp, cls.repo.id, cls.distributor.id)
            Task.wait_for_report(cls.pulp, response)
            unit = {
                'name': 'pike'
            }
            #install package on the consumer
            response = cls.consumer.install_unit(
                    cls.pulp,
                    unit,
                    'rpm',
                    options = {
                    "apply": True,
                    "reboot": False,
                    "importkeys": False
                    }

                )
            Task.wait_for_report(cls.pulp, response)
            # create scheduled update
            response=cls.consumer.schedule_update(cls.pulp,  schedule="PT1M", type_id='rpm',
                                                    unit_key={'name': 'pike'})
            cls.action = ScheduledAction.from_response(response)
            cls.delta = time.time() + 120


class SimpleScheduledUpdate(ConsumerScheduledUpdate):
    
    @agent_test(catching=True)
    def test_01_check_scheduled_update_works(self):
        while time.time() <= self.delta:
            time.sleep(1)
            self.action.reload(self.pulp)
            # total_run_count will be 2 as 'enabled' field is True by default
            # means that the scheduled sync is initially enabled
            if self.action.data["total_run_count"] == 2:
               break
        else:
            raise TaskTimeoutError('Waiting exceeded 120 second(s)', self.action.data)

    def test_02_get_non_existent_scheduled_update_bz1094647(self):
        with self.assertRaises(AssertionError):
            schedule = self.consumer.get_scheduled_action(self.pulp, '/content/update/', '11111111111')
        self.assertPulp(code=404)

    def test_02_get_scheduled_update(self):
        schedule = self.consumer.get_scheduled_action(self.pulp, '/content/update/', self.action.id)
        self.assertEqual(schedule.id, self.action.id)

    def test_03_list_scheduled_update(self):
        schedules = self.consumer.list_scheduled_action(self.pulp, '/content/update/')
        self.assertIn(self.action, schedules)

    def test_04_update_scheduled_update(self):
        self.action.update(self.pulp, data={'failure_threshold': 10})
        self.assertPulpOK()
        self.action.reload(self.pulp)
        self.assertTrue(self.action.data["failure_threshold"], 10)

    def test_05_delete_scheduled_update(self):
        self.action.delete(self.pulp)
        self.assertPulpOK()

    @expectedFailure
    def test_06_list_scheduled_update_bz1094634(self):
        schedules = self.consumer.list_scheduled_action(self.pulp, '/content/update/')
        self.assertEqual([], schedules)

