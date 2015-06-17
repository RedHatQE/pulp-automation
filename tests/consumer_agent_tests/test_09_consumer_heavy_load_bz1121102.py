import unittest, logging, nose
from tests.conf.roles import ROLES
from pulp_auto import Pulp, format_response
from pulp_auto.handler.profile import PROFILE
from tests.conf.facade.yum import YumRepo
from pulp_auto.consumer import (Consumer, Binding)
from pulp_auto.task import (Task, TaskFailure, TaskTimeoutError)
from pulp_auto.agent import Agent
from pulp_auto.qpid_handle import QpidHandle
from pulp_auto.authenticator import Authenticator
import pulp_auto.handler
from M2Crypto import (RSA, BIO)
from tests.pulp_test import requires, requires_any, PulpTest, agent_test


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

    def _tearDown(self):
        with self.pulp.asserting(True), \
            self.agent.catching(True), \
            self.agent.running(self.qpid_handle, frequency=10) \
        :
            Task.wait_for_report(self.pulp, self.repo.delete(self.pulp), timeout=20)

    def bindRepo(self):
        with self.pulp.asserting(True) :
            report = self.consumer.bind_distributor(self.pulp, self.repo.id, self.distributor.id)
            self.assertPulp(code=202)
            Task.wait_for_report(self.pulp, report, timeout=5)

    def test_01(self):
        errors = 0
        # change the range to 300-600 and run it separately from the rest of testcases
        for i in xrange(3):
            with self.agent.catching(True), self.agent.running(self.qpid_handle, frequency=10):
                try:
                    self.bindRepo()
                    self._tearDown()
                except (TaskFailure, TaskTimeoutError) as error:
                    print '> ',
                    errors += 1
                    print error
            repo_role = [repo for repo in self.ROLES.repos if repo.type == 'rpm'][0]
            self.repo, self.importer, [self.distributor] = YumRepo.from_role(repo_role).create(self.pulp)
            print i
        print "errors", errors
