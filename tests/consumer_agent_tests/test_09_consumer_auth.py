import unittest, logging, nose
from tests.conf.roles import ROLES
from pulp_auto import Pulp, format_response
from pulp_auto.handler.profile import PROFILE
from pulp_auto.consumer import (Consumer, Binding)
from pulp_auto.task import (Task, TaskFailure, TaskTimeoutError)
from pulp_auto.agent import Agent
from pulp_auto.qpid_handle import QpidHandle
from pulp_auto.authenticator import Authenticator
import pulp_auto.handler
from M2Crypto import (RSA, BIO)
from tests.pulp_test import requires, requires_any, PulpTest, agent_test
from tests.conf.facade.yum import YumRepo

@requires('qpid.url')
@requires_any('repos', lambda repo: repo.type == 'rpm')
class ConsumerAuthTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        super(ConsumerAuthTest, cls).setUpClass()
        cls.ROLES = ROLES
        cls.PROFILE = PROFILE
        cls.rsa_primary = RSA.load_key('/usr/share/pulp_auto/tests/data/fake-consumer.pem')
        cls.rsa_secondary = RSA.load_key('/usr/share/pulp_auto/tests/data/fake-consumer-secondary.pem')
        bio_fd = BIO.MemoryBuffer()
        cls.rsa_primary.save_pub_key_bio(bio_fd)
        cls.pub_pem_primary = bio_fd.getvalue()
        bio_fd = BIO.MemoryBuffer()
        cls.rsa_secondary.save_pub_key_bio(bio_fd)
        cls.pub_pem_secondary = bio_fd.getvalue()
        repo_role = [repo for repo in cls.ROLES.repos if repo.type == 'rpm'][0]
        cls.repo, cls.importer, [cls.distributor] = YumRepo.from_role(repo_role).create(cls.pulp)
        cls.consumer = Consumer.register(cls.pulp, cls.__name__ + '_consumer', rsa_pub=cls.pub_pem_primary)
        cls.agent = Agent(pulp_auto.handler, PROFILE=pulp_auto.handler.profile.PROFILE)
        cls.qpid_handle = QpidHandle(cls.ROLES.qpid.url, cls.consumer.id, auth=Authenticator(signing_key=cls.rsa_primary, verifying_key=cls.pulp.pubkey))

    @classmethod
    def tearDownClass(cls):
        with \
            cls.pulp.asserting(True), \
            cls.agent.catching(False), \
            cls.agent.running(cls.qpid_handle, frequency=10) \
        :
            Task.wait_for_report(cls.pulp, cls.repo.delete(cls.pulp))
            cls.consumer.delete(cls.pulp)
        super(ConsumerAuthTest, cls).tearDownClass()

    def tearDown(self):
        '''delete repo binding; runs within a "correct" agent running ctx'''
        with self.pulp.asserting(True), \
            self.agent.catching(True), \
            self.agent.running(self.qpid_handle, frequency=10) \
        :
            report = self.consumer.unbind_distributor(self.pulp, self.repo.id, self.distributor.id)
            self.assertPulp(code=202)
            Task.wait_for_report(self.pulp, report)

    def bindRepo(self):
        '''test cases are performed on a repo bind call; to be run within agent running ctx'''
        with self.pulp.asserting(True) :
            report = self.consumer.bind_distributor(self.pulp,self.repo.id, self.distributor.id)
            self.assertPulp(code=202)
            Task.wait_for_report(self.pulp, report, timeout=5)

    def test_01_valid_consumer_auth(self):
        with self.agent.catching(True), self.agent.running(self.qpid_handle, frequency=10):
            self.bindRepo()

    # bz: 1104788
    @unittest.expectedFailure
    def test_02_invalid_consumer_auth(self):
        invalid_qpid_handle = QpidHandle(self.ROLES.qpid.url, self.consumer.id, auth=Authenticator(signing_key=self.rsa_secondary, verifying_key=self.pulp.pubkey))
        with self.agent.catching(True), self.agent.running(invalid_qpid_handle, frequency=10):
            with self.assertRaises(TaskFailure):
                self.bindRepo()
