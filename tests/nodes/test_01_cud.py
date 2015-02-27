"""
simple nodes e2e scenario
"""
from tests.pulp_test import PulpTest, deleting, requires_any, ROLES
from pulp_auto.repo import create_yum_repo
from pulp_auto.task import Task
from tests.utils.upload import upload_url_rpm, temp_url, url_basename, download_package_with_dnf
from contextlib import closing
from pulp_auto.node import Node

@requires_any('nodes')
class NodeTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        super(NodeTest, cls).setUpClass()
        node_role = ROLES.nodes[0]
        cls.node = Node.register(cls.pulp,  node_role.id,
                display_name=getattr(node_role, 'display_name', None),
                description=getattr(node_role, 'description', None))

    @classmethod
    def tearDownClass(cls):
        cls.node.delete(cls.pulp)
        super(NodeTest, cls).tearDownClass()

    def test_01_deactivate(self):
        self.node.deactivate(self.pulp)

    def test_02_reactivate(self):
        self.node.activate(self.pulp)
