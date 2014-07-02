import pulp_test, json
from pulp_auto.user import User
from pulp_auto.permission import Permission
from pulp_auto import login, Pulp, format_response, format_preprequest
from pulp_auto.repo import Repo


def setUpModule():
    pass


class UserPermissionTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(UserPermissionTest, cls).setUpClass()
        cls.user = User(data={"login": cls.__name__ + "_user", "name": cls.__name__, "password": cls.__name__})
        cls.permission = Permission(data={"resource": "/v2/actions/login/"})
        # a new session has to be created for the user as auth credeantials of admin are used by default
        cls.user_pulp = Pulp(cls.pulp.url, auth=(cls.user.data['login'], cls.user.data['password']))


class SimpleUserPermissionTest(UserPermissionTest):

    def test_01_create_user(self):
        self.user.create(self.pulp)
        self.assertPulpOK()

    def test_02_grant_user_permission(self):
        self.user.grant_permission(self.pulp, self.user.id, "/", ["READ", "EXECUTE"])
        self.user.grant_permission(self.pulp, self.user.id, "/repositories/", ["READ", "EXECUTE"])
        self.assertPulpOK()

    def test_03_check_user_permission(self):
        #check that user can access resource on which permissions were granted
        with self.user_pulp.asserting(True):
            Repo.list(self.user_pulp)

    def test_04_search_users_id(self):
        # find user's login included in the list of permissions
        permissions = Permission.list(self.pulp, params={'resource': '/repositories/'})
        self.assertIn(self.user.data['login'], permissions[0].data['users'])

    def test_05_revoke_user_permission(self):
        self.user.revoke_permission(self.pulp, self.user.id, "/", ["READ", "EXECUTE"])
        self.user.revoke_permission(self.pulp, self.user.id, "/repositories/", ["READ", "EXECUTE"])
        self.assertPulpOK()

    def test_06_check_user_permission(self):
        #check that user cannot access resource as permissions were revoked
        with self.assertRaises(AssertionError):
            with self.user_pulp.asserting(True):
                Repo.list(self.user_pulp)

    def test_07_delete_user(self):
        self.user.delete(self.pulp)
        self.assertPulpOK()

    def test_08_create_permission(self):
        #verify that new permission cannot be created
        with self.assertRaises(TypeError):
            with self.pulp.asserting(True):
                self.permission.create(self.pulp)

    def test_09_grant_unexistant_user_permission(self):
        self.user.grant_permission(self.pulp, "UnexistantLogin", "/", ["EXECUTE"])
        self.assertPulp(code=404)

    def test_10_grant_invalid_params(self):
        self.user.grant_permission(self.pulp, self.user.id, "/", ["INVALID"])
        self.assertPulp(code=400)

    def test_11_revoke_unexistant_user_permis(self):
        self.user.revoke_permission(self.pulp, "UnexistantLogin", "/", ["EXECUTE"])
        self.assertPulp(code=404)

    def test_12_revoke_invalid_params(self):
        self.user.revoke_permission(self.pulp, self.user.id, "/", ["INVALID"])
        self.assertPulp(code=400)

    def test_13_list_permissions(self):
        # check that after deletion of all users permissions were also revoked
        permissions = Permission.list(self.pulp)
        self.assertPulp(code=200)
        # so permissions only for admin user should stay
        for i in range(0, len(permissions)):
            self.assertTrue("admin" in permissions[i].data['users'] and len(permissions[i].data['users']) == 1)
