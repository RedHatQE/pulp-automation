import pulp_test, json
from pulp_auto.status import Status

def setUpModule():
    pass

class StatusTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(StatusTest, cls).setUpClass()
        cls.status = Status(data={'id': ""})

class SimpleStatusTest(StatusTest):
    
    def test_01_get_server_status(self):
        s = self.status.get_status(self.pulp)
        self.assertPulp(code=200)

