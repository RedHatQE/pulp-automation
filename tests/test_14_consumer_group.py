import pulp_test, json
from pulp_auto.consumer_group import ConsumerGroup 

def setUpModule():
    pass

class ConsumerGroupTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(ConsumerGroupTest, cls).setUpClass()
        cls.consumer_group = ConsumerGroup(data={'id': cls.__name__ + "_consumer_group"})

class SimpleConsumerGroupTest(ConsumerGroupTest):

    def test_01_create_group(self):
        self.consumer_group.create(self.pulp)
        self.assertPulpOK()
        
    def test_02_update_group(self):
        display_name = 'A %s group' % self.__class__.__name__
        self.consumer_group.update(self.pulp, {'display_name': display_name})
        self.assertPulp(code=200)
        self.assertEqual(ConsumerGroup.get(self.pulp, self.consumer_group.id).data['display_name'], display_name)
            
    def test_0X_delete_goup(self):
        self.consumer_group.delete(self.pulp)
        self.assertPulpOK()
