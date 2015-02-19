from pulp_auto.event_listener import EventListener
from tests.pulp_test import PulpTest, deleting

try:
    from requestbin.bin import Bin
except ImportError as e:
        import unittest
        raise unittest.SkipTest(e)


class EventListenerTest(PulpTest):

    @classmethod
    def setUpClass(cls):
        PulpTest.setUpClass()
        # set up a fresh service bin common to this class tests
        cls.bin = Bin.create()

    def test_01_cud(self):
        # instantiate default http listener
        el0 = EventListener.http(self.bin.url)
        response = el0.create(self.pulp)
        self.assertPulpOK()
        # update the listener
        with deleting(self.pulp, EventListener.from_response(response)) as el1:
            # get listener
            assert EventListener.get(self.pulp, el1.id) == el1, 'failed fetching %s' % el1
            # list listeners
            assert el1 in EventListener.list(self.pulp), 'failed listing %s' % el1
            # assert updating works
            el1.update(self.pulp, {'event_types': ['repo.sync.finish', 'repo.sync.start']})
            self.assertPulpOK()
            el1.reload(self.pulp)
            assert sorted(el1.data['event_types']) == \
                        sorted(['repo.sync.finish', 'repo.sync.start']), 'update failed: %s' % el1
