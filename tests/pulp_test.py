# basic pulp test class
import unittest, pprint, logging, nose
from . import ROLES
from pulp_auto import Pulp, format_response
from pulp_auto.handler.profile import PROFILE
from pulp_auto.consumer import (Consumer, Binding)
from pulp_auto.repo import create_yum_repo
from pulp_auto.units import Orphans
from pulp_auto.task import Task
from pulp_auto.agent import Agent
from pulp_auto.qpid_handle import QpidHandle
import pulp_auto.handler
from pulp_auto.namespace import (locate_ns_item,)
from pulp_auto.authenticator import Authenticator
from M2Crypto import (RSA, BIO)
from contextlib import contextmanager


def requires(*things):
    '''skip test case unless there is thing in ROLES'''
    try:
        for thing in things:
            locate_ns_item(ROLES, thing)
    except KeyError:
        return unittest.skip("no %r found in ROLES" % thing)
    return lambda function: function

def requires_any(thing, condition=lambda item: True):
    '''skip test case unless there are any thing items ROLES for which the condition holds'''
    @requires(thing)
    def wrapped():
        '''create propper decorator --- either skipping one or "empty" one'''
        if not any(map(condition, locate_ns_item(ROLES, thing))):
            return unittest.skip("no suitable items found in ROLES.%s" % thing)
        return lambda function: function
    return wrapped()


@requires('pulp.url', 'pulp.auth', 'pulp.verify_api_ssl')
class PulpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if getattr(cls, '__unittest_skip__', False):
            # FIXME: suggest a unittest patch dealing setUpClass being called even though __unittest_skip__ is set
            raise unittest.SkipTest(getattr(cls, '__unittest_skip_why__', ''))
        cls.pulp = Pulp(ROLES.pulp.url, tuple(ROLES.pulp.auth), ROLES.pulp.verify_api_ssl)
        cls.log = logging.getLogger(cls.__name__)

    def assertPulpOK(self):
        self.assertTrue(
            self.pulp.is_ok,
            "pulp was not OK:\n%s" % format_response(self.pulp.last_response)
        )

    def assertPulp(self, code=200, data={}):
        self.assertEqual(
            self.pulp.last_response.status_code,
            code
        )
        response_data = self.pulp.last_response.json()
        for k, v in data:
            self.assertIn(k, response_data)
            self.assertEqual(v, response_data[k])

    def assertEqual(self, a, b, msg=None):
        if msg is None:
            super(PulpTest, self).assertEqual(a, b, pprint.pformat("%r != %r" % (a, b)))
        else:
            super(PulpTest, self).assertEqual(a, b, msg)

    @classmethod
    def tearDownClass(cls):
        '''nothing to do'''
        pass



@nose.tools.nottest
def agent_test(catching=False, frequency=1):
    def decorator_maker(method):
        import functools

        @nose.plugins.attrib.attr('agent_test')
        @nose.tools.make_decorator(method)
        def decorated_method(self):
            with self.agent.catching(catching):
                with self.agent.running(self.qpid_handle, frequency=frequency):
                    ret = method(self)
            return ret
        return decorated_method
    return decorator_maker


@requires('qpid.url')
@requires_any('repos', lambda repo: repo.type == 'rpm')
class ConsumerAgentPulpTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        super(ConsumerAgentPulpTest, cls).setUpClass()
        cls.ROLES = ROLES
        cls.PROFILE = PROFILE
        from . import ROLES as inventory_roles
        cls.repo, cls.importer, cls.distributor = create_yum_repo(cls.pulp, **[repo for repo in inventory_roles.repos if repo.type == 'rpm'][0])
        cls.rsa = RSA.load_key('./tests/data/fake-consumer.pem')
        bio_fd = BIO.MemoryBuffer()
        cls.rsa.save_pub_key_bio(bio_fd)
        cls.rsa_pub_pem = bio_fd.getvalue()
        cls.consumer = Consumer.register(cls.pulp, cls.__name__ + '_consumer', rsa_pub=cls.rsa_pub_pem)
        #cls.binding_data = {'repo_id': cls.repo.id, 'distributor_id': cls.distributor.id}
        cls.log.info('instantiating agent')
        cls.agent = Agent(pulp_auto.handler, PROFILE=pulp_auto.handler.profile.PROFILE)
        cls.log.info('instantiating qpid handle')
        cls.qpid_handle = QpidHandle(ROLES.qpid.url, cls.consumer.id, auth=Authenticator(signing_key=cls.rsa, verifying_key=cls.pulp.pubkey))

    @classmethod
    def tearDownClass(cls):
        with \
            cls.pulp.asserting(True), \
            cls.agent.catching(False), \
            cls.agent.running(cls.qpid_handle, frequency=10) \
        :
            Task.wait_for_report(cls.pulp, cls.repo.delete(cls.pulp))
            Task.wait_for_report(cls.pulp, Orphans.delete(cls.pulp))
            cls.consumer.delete(cls.pulp)
        super(ConsumerAgentPulpTest, cls).tearDownClass()


class InventoryInducedSkip(unittest.SkipTest):
        '''some inventory items are missing --- skip the test that requires these'''

def stacked_ctx(ctxmanager):
    '''decorator allowing simple ctx managers to get stacked'''
    @contextmanager
    def stacked(*things):
        if len(things) > 1:
            with ctxmanager(things[0]) as thing:
                with stacked(*things[1:]) as somethings:
                    yield thing, somethings
        else:
            with ctxmanager(things[0]) as thing:
                yield thing
    return stacked

@contextmanager
def calling_method(thing, method, *args, **kvs):
    '''call thing.<method>(*args, **kvs) upon exit'''
    try:
        yield thing
    finally:
        getattr(thing, method)(*args, **kvs)

@contextmanager
def deleting(pulp, *things):
    '''call thing.delete(pulp) upon return for thing in things'''

    @stacked_ctx
    @contextmanager
    def wrapper_ctx(thing):
        with calling_method(thing, 'delete', pulp) as thing:
            yield thing
        assert pulp.is_ok, 'deleting %s caused pulp not feeling ok: %s' % \
                (thing, pulp.last_response)

    with wrapper_ctx(*things) as otherthings:
        yield otherthings

def temp_url(url, chunksize=65535):
    '''save the url as a temporary named file object'''
    import tempfile
    import urllib2
    fd = urllib2.urlopen(url)
    tmpfd = tempfile.NamedTemporaryFile()
    while True:
        data = fd.read(chunksize)
        if not data:
            break
        tmpfd.write(data)
    tmpfd.file.seek(0)
    fd.close()
    return tmpfd
