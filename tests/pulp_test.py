# basic pulp test class
import unittest, pprint, logging
from . import ROLES
from pulp import Pulp, format_response
from pulp.handler.profile import PROFILE
from pulp.consumer import (Consumer, Binding)
from pulp.repo import create_yum_repo
from pulp.task import Task
from pulp.agent import Agent
from pulp.qpid_handle import QpidHandle
import pulp.handler

class PulpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pulp = Pulp(ROLES.pulp.url, tuple(ROLES.pulp.auth))
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

def agent_test(catching=False, frequency=1):
    def decorator_maker(method):
        import functools
        @functools.wraps(method)
        def decorated_method(self):
            with self.agent.catching(catching):
                with self.agent.running(self.qpid_handle, frequency=frequency):
                    ret = method(self)
            return ret
        return decorated_method
    return decorator_maker

class ConsumerAgentPulpTest(PulpTest):
    repo_feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'

    @classmethod
    def setUpClass(cls):
        super(ConsumerAgentPulpTest, cls).setUpClass()
        cls.ROLES = ROLES
        cls.PROFILE = PROFILE
        cls.repo, cls.importer, cls.distributor = create_yum_repo(
            cls.pulp,
            cls.__name__ + "_repo",
            cls.repo_feed,
            '/' + cls.__name__ + '_repo/zoo/'
        )
        cls.consumer = Consumer({'id': cls.__name__ + '_consumer'})
        cls.consumer.create(cls.pulp)
        cls.binding_data = {'repo_id': cls.repo.id, 'distributor_id': cls.distributor.id}
        cls.log.info('instantiating agent')
        cls.agent = Agent(pulp.handler, PROFILE=pulp.handler.profile.PROFILE)
        cls.log.info('instantiating qpid handle')
        cls.qpid_handle = QpidHandle(ROLES.qpid.url, cls.consumer.id)

    @classmethod
    def tearDownClass(cls):
        with \
            cls.pulp.asserting(True), \
            cls.agent.catching(False), \
            cls.agent.running(cls.qpid_handle, frequency=10) \
        :
            Task.wait_for_response(cls.pulp, cls.repo.delete(cls.pulp))
            cls.consumer.delete(cls.pulp)
        super(ConsumerAgentPulpTest, cls).tearDownClass()



