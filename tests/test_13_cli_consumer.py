from pulp_auto.consumer import (Cli, RpmUnit, YumRepo, RpmRepo, Consumer) 
from pulp_auto.task import Task
from pulp_auto.repo import create_yum_repo
from pulp_test import (PulpTest, InventoryInducedSkip)
from . import ROLES

def setUpModule():
    '''sanity check roles'''
    try:
        ROLES.pulp, ROLES.consumers
    except AttributeError as e:
        raise InventoryInducedSkip(e.message)
    
    if not ROLES.consumers:
        raise InventoryInducedSkip("empty ROLES.consumers list")

def tearDownModule():
    pass

class CliConsumerTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        super(CliConsumerTest, cls).setUpClass()
        consumer_config = ROLES.consumers[0]
        with cls.pulp.asserting(True):
            cls.repo, _, _ = create_yum_repo( \
                cls.pulp,
                consumer_config.repos[0].id, \
                consumer_config.repos[0].feed, \
                **consumer_config.repos[0].config \
            )
        cls.consumer = Cli.ready_instance(**consumer_config)

    def test_01_api_registered_consumer(self):
        # assert the cli registration worked in API
        Consumer.get(self.pulp, self.consumer.consumer_id)
        self.assertPulpOK()

    @classmethod
    def tearDownClass(cls):
        cls.repo.delete(cls.pulp)
        cls.consumer.unregister()
        super(CliConsumerTest, cls).tearDownClass()
