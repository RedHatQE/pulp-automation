"""
simple nodes e2e scenario
"""
from tests.pulp_test import PulpTest, deleting, requires_any, ROLES
from pulp_auto.pulp import Pulp, ResponseLike
from pulp_auto.login import request as login_request
from pulp_auto.repo import create_yum_repo, NodeDistributor
from pulp_auto.task import Task
from pulp_auto.common_consumer import Binding
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
                description=getattr(node_role, 'description', None),
                display_name=getattr(node_role, 'display_name', None))
        cls.pulp_child = Pulp(node_role.url, tuple(node_role.auth), node_role.verify_api_ssl)

    @classmethod
    def tearDownClass(cls):
        with deleting(cls.pulp, cls.node):
            pass
        super(NodeTest, cls).tearDownClass()

class NodeTestActivation(NodeTest):
    def test_01_activate(self):
        self.node.activate(self.pulp)
        self.assertPulpOK()
        self.node.reload(self.pulp)

    def test_02_deactivate(self):
        self.node.deactivate(self.pulp)
        self.assertPulpOK()
        self.node.reload(self.pulp)

    def test_03_reactivate(self):
        self.node.activate(self.pulp)
        self.assertPulpOK()
        self.node.reload(self.pulp)

    def test_04_list(self):
        assert self.node in Node.list(self.pulp), 'node %s not found on pulp' % self.node.id

    def test_05_login(self):
        self.pulp_child.send(login_request())
        self.assertPulpOK()


@requires_any('repos', lambda repo: repo.type == 'rpm')
class NodeTestRepo(NodeTest):

    @classmethod
    def setUpClass(cls):
        # set up the class with a repo that is synced and set up for nodes to feed from
        super(NodeTestRepo, cls).setUpClass()
        cls.node.activate(cls.pulp)
        repo_role = ROLES.repos[0]
        cls.repo, cls.importer, cls.distributor = create_yum_repo(cls.pulp, **repo_role)
        Task.wait_for_report(cls.pulp, cls.repo.sync(cls.pulp))
        response = cls.repo.associate_distributor(cls.pulp, NodeDistributor.default().data)
        cls.node_distributor = NodeDistributor.from_response(response)

    @classmethod
    def tearDownClass(cls):
        cls.node.deactivate(cls.pulp)
        with deleting(cls.pulp, cls.repo, cls.importer, cls.distributor, cls.node_distributor):
            pass
        super(NodeTestRepo, cls).tearDownClass()

    def test_01_node_distributor_present(self):
        # bless
        assert self.node_distributor in self.repo.list_distributors(self.pulp), \
            'Node Distributor not found'

    def test_02_node_distributor_publish(self):
        self.repo.publish(self.pulp, self.node_distributor.id)
        self.assertPulpOK()

    def test_03_node_bind_repo(self):
        response = self.node.bind_repo(self.pulp, self.repo.id, self.node_distributor.id)
        self.assertPulpOK()

    def test_99_node_unbind_repo(self):
        self.node.unbind_repo(self.pulp, self.repo.id, self.node_distributor.id)
        self.assertPulpOK()
