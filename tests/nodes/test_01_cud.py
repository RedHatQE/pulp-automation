"""
simple nodes e2e scenario
"""
from contextlib import closing
from pulp_auto.pulp import Pulp, ResponseLike
from pulp_auto.consumer import Cli
from pulp_auto.login import request as login_request
from pulp_auto.repo import NodeDistributor, Repo
from pulp_auto.task import Task
from pulp_auto.common_consumer import Binding
from pulp_auto.node import Node
from tests.utils.upload import upload_url_rpm, temp_url, url_basename, download_package_with_dnf, \
        pulp_repo_url
from tests.pulp_test import PulpTest, deleting, requires_any
from tests.conf.roles import ROLES
from tests.conf.facade.yum import YumRepo, YumImporter, YumDistributor


@requires_any('nodes')
class NodeTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        super(NodeTest, cls).setUpClass()
        node_role = ROLES.nodes[0]
        # configure the node via cli
        cli = Cli.ready_instance(**node_role)
        cls.node = Node.get(cls.pulp,  node_role.id)
        cls.node.cli = cli
        # instantiate a pulp child from the role details
        cls.pulp_child = Pulp(node_role.url, tuple(node_role.auth), node_role.verify_api_ssl)

    @classmethod
    def tearDownClass(cls):
        cls.node.cli.unregister()
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
    # end2end scenario with a child node binding&syncing an rpm repo
    @classmethod
    def setUpClass(cls):
        # set up the class with a repo that is synced and set up for nodes to feed from
        super(NodeTestRepo, cls).setUpClass()
        cls.node.activate(cls.pulp)
        repo_role = ROLES.repos[0]
        cls.repo, cls.importer, [cls.distributor] = YumRepo.from_role(repo_role).create(cls.pulp)
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
        response = self.repo.publish(self.pulp, self.node_distributor.id)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_03_node_bind_repo(self):
        response = self.node.bind_repo(self.pulp, self.repo.id, self.node_distributor.id)
        self.assertPulpOK()

    def test_04_child_repo_sync(self):
        response = self.node.sync_repo(self.pulp, self.repo.id)
        self.assertPulpOK()
        Task.wait_for_report(self.pulp, response)

    def test_05_child_repo_list(self):
        # at this point the repo should be visible on both the nodes
        assert self.repo in Repo.list(self.pulp_child), 'repo not propagated to child node'

    def test_06_child_repo_content(self):
        # access the content of the pulp_child node
        # please note when the repo is created on the other node,
        # the distributor id used by default is yum_distributor

        # make sure the repo was published on the child node
        # the repo ID and distributor ID are the same on both the nodes
        child_repo = Repo.get(self.pulp_child, self.repo.id)
        response = child_repo.publish(self.pulp_child, self.distributor.id)
        assert response == ResponseLike(202), 'wrong response from the child node: %s' % response
        Task.wait_for_report(self.pulp_child, response)

        # fetch the repo content url on the child node
        repo_url = pulp_repo_url(self.pulp_child, self.repo.id)
        assert repo_url, 'invalid repo id on pulp_child node'
        # try accessing the content on the child node
        pkg_name = download_package_with_dnf(self.pulp_child, repo_url, 'bear')
        assert pkg_name == 'bear', 'not able to acces bear rpm on the child node'

    def test_99_node_unbind_repo(self):
        self.node.unbind_repo(self.pulp, self.repo.id, self.node_distributor.id)
        self.assertPulpOK()
        # nodes keep the repos after updating
        child_repos = Repo.list(self.pulp_child)
        for repo in child_repos:
            Task.wait_for_report(self.pulp_child, repo.delete(self.pulp_child))
