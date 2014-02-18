import pulp_test
from pulp_auto import login, Pulp


def setUpModule():
    pass


class TestLogin(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(TestLogin, cls).setUpClass()
        cls.wrong_pulp = Pulp(cls.pulp.url, auth=('admin', 'xxx'))


class SimpleTestLogin(TestLogin):

    def test_login(self):
        self.pulp.send(login.request())
        self.assertPulpOK()

    def test_wrong_login(self):
        with self.assertRaises(AssertionError):
            with self.wrong_pulp.asserting(True):
                self.wrong_pulp.send(login.request())
