import pulp_test, json
from pulp_auto.user import User
from pulp_auto.permission import Permission
from pulp_auto import login, Pulp, format_response, format_preprequest
from pulp_auto.repo import Repo
from pulp_auto.role import Role


def setUpModule():
    pass


class RolePermissionTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RolePermissionTest, cls).setUpClass()
        cls.user = User(data={"login": cls.__name__ + "_user", "name": cls.__name__, "password": cls.__name__})
        cls.user2 = User(data={"login": cls.__name__ + "_user2", "name": cls.__name__, "password": cls.__name__})
        cls.permission = Permission(data={"resource": "/v2/actions/login/"})
        # a new session has to be created for the user as auth credeantials of admin are used by default
        cls.user_pulp = Pulp(cls.pulp.url, auth=(cls.user.data['login'], cls.user.data['password']))
        cls.user_pulp2 = Pulp(cls.pulp.url, auth=(cls.user2.data['login'], cls.user2.data['password']))

        # create roles
        with cls.pulp.asserting(True):
            response = Role.create(cls.pulp, data={'role_id': cls.__name__ + "_role"})
        cls.role = Role.from_response(response)

        with cls.pulp.asserting(True):
            response = Role.create(cls.pulp, data={'role_id': cls.__name__ + "_role2"})
        cls.role2 = Role.from_response(response)

    @classmethod
    def tearDownClass(cls):
        # delete users
        with cls.pulp.asserting(True):
            cls.user.delete(cls.pulp)
        with cls.pulp.asserting(True):
            cls.user2.delete(cls.pulp)

        # delete roles
        with cls.pulp.asserting(True):
            cls.role.delete(cls.pulp)
        with cls.pulp.asserting(True):
            cls.role2.delete(cls.pulp)


class SimpleRolePermissionTest(RolePermissionTest):

    def test_01_grant_role_permission(self):
        self.role.grant_permission(self.pulp, self.role.id, "/", ["READ", "EXECUTE"])
        self.role.grant_permission(self.pulp, self.role.id, "/repositories/", ["READ", "EXECUTE"])
        self.assertPulpOK()

    def test_02_grant_unexistant_role_permission(self):
        self.role.grant_permission(self.pulp, "UnexistantRole", "/", ["EXECUTE"])
        self.assertPulp(code=404)

    def test_03_grant_invalid_params(self):
        self.role.grant_permission(self.pulp, self.role.id, "/", ["INVALID"])
        self.assertPulp(code=400)

    def test_04_check_role_permission(self):
        # create users
        self.user.create(self.pulp)
        self.assertPulpOK()

        self.user2.create(self.pulp)
        self.assertPulpOK()

        # add users to the role
        self.role.add_user(
            self.pulp,
            self.user.id
        )
        self.assertPulp(code=200)

        self.role.add_user(
            self.pulp,
            self.user2.id
        )
        self.assertPulp(code=200)

        # check users' permissions, that thay can access resource after been added to specific role
        with self.user_pulp.asserting(True):
            Repo.list(self.user_pulp)

        with self.user_pulp2.asserting(True):
            Repo.list(self.user_pulp2)

    def test_05_search_users_id(self):
        # find user's login included in the list of permissions
        permissions = Permission.list(self.pulp, params={'resource': '/repositories/'})
        self.assertIn(self.user.id, permissions[0].data['users'])

    def test_06_revoke_role_permission(self):
        self.role.revoke_permission(self.pulp, self.role.id, "/", ["READ", "EXECUTE"])
        self.role.revoke_permission(self.pulp, self.role.id, "/repositories/", ["READ", "EXECUTE"])
        self.assertPulpOK()

    def test_07_check_role_permission(self):
        # check that user cannot access resource as permissions of the role were revoked
        with self.assertRaises(AssertionError):
            with self.user_pulp.asserting(True):
                Repo.list(self.user_pulp)

    def test_08_revoke_unexistant_role_permis(self):
        self.role.revoke_permission(self.pulp, "UnexistantLogin", "/", ["EXECUTE"])
        self.assertPulp(code=404)

    def test_09_revoke_invalid_params(self):
        self.role.revoke_permission(self.pulp, self.role.id, "/", ["INVALID"])
        self.assertPulp(code=400)

    def test_10_delete_users(self):
        # delete users
        self.user.delete(self.pulp)
        self.assertPulpOK()

        self.user2.delete(self.pulp)
        self.assertPulpOK()

    def test_11_two_roles_two_users(self):
        # create users
        self.user.create(self.pulp)
        self.assertPulpOK()

        self.user2.create(self.pulp)
        self.assertPulpOK()

        # grant permissions
        self.role.grant_permission(self.pulp, self.role.id, "/", ["READ", "EXECUTE"])
        self.role.grant_permission(self.pulp, self.role.id, "/repositories/", ["READ", "EXECUTE"])
        self.assertPulpOK()

        self.role2.grant_permission(self.pulp, self.role2.id, "/", ["READ", "EXECUTE"])
        self.role2.grant_permission(self.pulp, self.role2.id, "/repositories/", ["READ", "EXECUTE"])
        self.assertPulpOK()

        # add users to roles
        self.role.add_user(
            self.pulp,
            self.user.id
        )
        self.assertPulp(code=200)

        self.role2.add_user(
            self.pulp,
            self.user.id
        )
        self.assertPulp(code=200)

        self.role2.add_user(
            self.pulp,
            self.user2.id
        )
        self.assertPulp(code=200)

        # check users' permissions
        with self.user_pulp.asserting(True):
            Repo.list(self.user_pulp)

        with self.user_pulp2.asserting(True):
            Repo.list(self.user_pulp2)

        # revoke permissions from role2
        self.role2.revoke_permission(self.pulp, self.role2.id, "/", ["READ", "EXECUTE"])
        self.role2.revoke_permission(self.pulp, self.role2.id, "/repositories/", ["READ", "EXECUTE"])
        self.assertPulpOK()

        # check users' permissions
        # user should still be able to access resource as it belongs to other role
        with self.user_pulp.asserting(True):
            Repo.list(self.user_pulp)
        # user2 should not be able to access resource as no more pemissions are granted to it
        with self.assertRaises(AssertionError):
            with self.user_pulp2.asserting(True):
                Repo.list(self.user_pulp2)
