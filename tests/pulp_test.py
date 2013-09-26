# basic pulp test class
import unittest, pprint
from . import ROLES
from pulp import Pulp


class PulpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pulp = Pulp(ROLES.pulp.url, tuple(ROLES.pulp.auth))

    def assertPulpOK(self):
       self.assertTrue(self.pulp.is_ok, "pulp was not OK: %s" % pprint.pformat(self.pulp.last_result.json()))
