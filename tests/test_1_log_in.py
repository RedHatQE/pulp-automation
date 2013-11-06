import pulp_test
from pulp import login


class TestLogin(pulp_test.PulpTest):

    def test_login(self):
        self.pulp.send(login.request())
        self.assertPulpOK()
