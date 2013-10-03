# basic pulp test class
import unittest, pprint
from . import ROLES
from pulp import Pulp, format_response


class PulpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pulp = Pulp(ROLES.pulp.url, tuple(ROLES.pulp.auth))

    def assertPulpOK(self):
        self.assertTrue(
            self.pulp.is_ok,
            "pulp was not OK:\n%s" % format_response(self.pulp.last_response)
        )

    def assertPulpStatusCode(code=200):
        self.assertEqual(
            self.pulp.last_response.status_code,
            code
        )

    def assertEqual(self, a, b, msg=None):
        if msg is None:
            super(PulpTest, self).assertEqual(a, b, pprint.pformat("%r != %r" % (a, b)))
        else:
            super(PulpTest, self).assertEqual(a, b, msg)
