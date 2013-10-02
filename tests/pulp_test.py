# basic pulp test class
import unittest, pprint
from . import ROLES
from pulp import Pulp


class PulpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pulp = Pulp(ROLES.pulp.url, tuple(ROLES.pulp.auth))

    def assertPulpOK(self):
        self.assertTrue(
            self.pulp.is_ok,
            "pulp was not OK: %s\n\turl: %s" % (pprint.pformat(self.pulp.last_result.text), self.pulp.last_result.url)
        )

    def assertEqual(self, a, b, msg=None):
        if msg is None:
            super(PulpTest, self).assertEqual(a, b, pprint.pformat("%r != %r" % (a, b)))
        else:
            super(PulpTest, self).assertEqual(a, b, msg)
