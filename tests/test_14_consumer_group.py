import pulp_test, json
from pulp_auto.consumer_group import ConsumerGroup 
from pulp_auto.consumer.consumer_class import Consumer
from pulp_auto.task import Task
from pulp_test import (ConsumerAgentPulpTest, agent_test)

def setUpModule():
    pass

class ConsumerGroupTest(ConsumerAgentPulpTest):
    @classmethod
    def setUpClass(cls):
        super(ConsumerGroupTest, cls).setUpClass()
        cls.consumer_group = ConsumerGroup(data={'id': cls.__name__ + "_consumer_group"})
        cls.consumer_group1 = ConsumerGroup(data={'id': cls.__name__ + "_consumer_group1", "consumer_ids":["some_consumer"]})

class SimpleConsumerGroupTest(ConsumerGroupTest):

    def test_01_create_group(self):
        self.consumer_group.create(self.pulp)
        self.assertPulpOK()

    def test_01_create_group_with_invalid_consumer_1074661(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1074661
        self.consumer_group1.create(self.pulp)
        self.assertPulp(code=400)
        
    def test_02_update_group(self):
        display_name = 'A %s group' % self.__class__.__name__
        self.consumer_group.update(self.pulp, {'display_name': display_name})
        self.assertPulp(code=200)
        self.assertEqual(ConsumerGroup.get(self.pulp, self.consumer_group.id).data['display_name'], display_name)
        
    @agent_test(catching=True)
    def test_03_associate_consumer(self):
        response = self.consumer_group.associate_consumer(self.pulp, data={"criteria": {"filters": {"id": self.consumer.id}}})
        self.assertPulp(code=200)
        self.assertIn(self.consumer.id, response.json())

    @agent_test(catching=True)
    def test_03_associate_consumer_to_nonexistent_group(self):
        response = self.consumer_group1.associate_consumer(self.pulp, data={"criteria": {"filters": {"id": self.consumer.id}}})
        self.assertPulp(code=404)
        
    def test_04_unassociate_consumer(self):
        response = self.consumer_group.unassociate_consumer(self.pulp, data={"criteria": {"filters": {"id": self.consumer.id}}})
        self.assertPulp(code=200)
        self.assertEqual(response.json(), [])

    def test_04_unassociate_consumer_from_nonexistent_group(self):
        response = self.consumer_group1.unassociate_consumer(self.pulp, data={"criteria": {"filters": {"id": self.consumer.id}}})
        self.assertPulp(code=404)

    def test_05_delete_goup(self):
        self.consumer_group.delete(self.pulp)
        self.assertPulpOK()
        
