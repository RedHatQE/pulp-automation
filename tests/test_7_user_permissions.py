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
        self.user.grant_permission(self.pulp, data={"login": self.user.data['login'], "resource": "/", "operations": ["READ", "EXECUTE"]})
        self.user.grant_permission(self.pulp, data={"login": self.user.data['login'], "resource": "/repositories/", "operations": ["READ", "EXECUTE"]})
        self.assertPulpOK()

    def test_03_check_user_permission(self):
        #check that user can access resource on which permissions were granted
        with self.user_pulp.asserting(True):
            Repo.list(self.user_pulp)

    def test_04_revoke_user_permission(self):
        self.user.revoke_permission(self.pulp, data={"login": self.user.data['login'], "resource": "/", "operations": ["READ", "EXECUTE"]})
        self.user.revoke_permission(self.pulp, data={"login": self.user.data['login'], "resource": "/repositories/", "operations": ["READ", "EXECUTE"]})
        self.assertPulpOK()

    def test_05_check_user_permission(self):
        #check that user cannot access resource as permissions were revoked
        with self.assertRaises(AssertionError):
            with self.user_pulp.asserting(True):
                Repo.list(self.user_pulp)

    def test_06_delete_user(self):
        self.user.delete(self.pulp)
        self.assertPulpOK()

    def test_07_create_permission(self):
        #verify that new permission cannot be created
        with self.assertRaises(TypeError):
            with self.pulp.asserting(True):
                self.permission.create(self.pulp)

    def test_08_grant_unexistant_user_permission(self):
        self.user.grant_permission(self.pulp, data={"login": "UnexistantLogin", "resource": "/", "operations": ["EXECUTE"]})
        self.assertPulp(code=404)

    def test_09_list_permissions(self):
        Permission.list(self.pulp)
        self.assertPulp(code=200)
        #FIXME figure out how to AssertIn user id in the list of permissions
