"""
simple nodes e2e scenario
"""
from tests.pulp_test import PulpTest, deleting, requires_any, ROLES
from pulp_auto.pulp import Pulp
from pulp_auto.login import request as login_request
from pulp_auto.repo import create_yum_repo
from pulp_auto.task import Task
from tests.utils.upload import upload_url_rpm, temp_url, url_basename, download_package_with_dnf
from contextlib import closing
from pulp_auto.node import Node

@requires_any('nodes')
@requires_any('repos', lambda repo: repo.type == 'rpm')
class NodeTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        super(NodeTest, cls).setUpClass()
        node_role = ROLES.nodes[0]
        cls.node = Node.register(cls.pulp,  node_role.id,
                description=getattr(node_role, 'description', None),
                display_name=getattr(node_role, 'display_name', None))
        cls.pulp_node = Pulp(node_role.url, tuple(node_role.auth), node_role.verify_api_ssl)
        repo_role = ROLES.repos[0]
        cls.repo, cls.importer, cls.distributor = create_yum_repo(cls.pulp, **repo_role)

    @classmethod
    def tearDownClass(cls):
        with deleting(cls.pulp, cls.node, cls.repo, cls.importer, cls.distributor):
            pass
        super(NodeTest, cls).tearDownClass()

    def test_01_deactivate(self):
        self.node.deactivate(self.pulp)

    def test_02_reactivate(self):
        self.node.activate(self.pulp)

    def test_03_list(self):
        assert self.node in Node.list(self.pulp), 'node %s not found on pulp' % self.node.id

    def test_04_login(self):
        self.pulp_node.send(login_request())
        self.assertPulpOK()
