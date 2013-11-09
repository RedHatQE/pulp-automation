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
        self.role.grant_permission(self.pulp, data={"role_id": self.role.data['id'], "resource": "/", "operations": ["READ", "EXECUTE"]})
        self.role.grant_permission(self.pulp, data={"role_id": self.role.data['id'], "resource": "/repositories/", "operations": ["READ", "EXECUTE"]})
        self.assertPulpOK()
        
    def test_02_check_role_permission(self):
        # create users
        self.user.create(self.pulp)
        self.assertPulpOK()
        
        self.user2.create(self.pulp)
        self.assertPulpOK()
        
        # add users to the role
        self.role.add_user(
            self.pulp,
            data={'login': self.user.data['login']}
        )
        self.assertPulp(code=200)
        
        self.role.add_user(
            self.pulp,
            data={'login': self.user2.data['login']}
        )
        self.assertPulp(code=200)
        
        # check users' permissions
        with self.user_pulp.asserting(True):
            Repo.list(self.user_pulp)
            
        with self.user_pulp2.asserting(True):
            Repo.list(self.user_pulp2)
            
    def test_03_revoke_role_permission(self):
        self.role.revoke_permission(self.pulp, data={"role_id": self.role.data['id'], "resource": "/", "operations": ["READ", "EXECUTE"]})
        self.role.revoke_permission(self.pulp, data={"role_id": self.role.data['id'], "resource": "/repositories/", "operations": ["READ", "EXECUTE"]})
        self.assertPulpOK()
        
    def test_04_check_role_permission(self):
        # check that user cannot access resource as permissions were revoked
        with self.assertRaises(AssertionError):
            with self.user_pulp.asserting(True):
                Repo.list(self.user_pulp)

    def test_05_delete_users(self):
        # delete users 
        self.user.delete(self.pulp)
        self.assertPulpOK()
        
        self.user2.delete(self.pulp)
        self.assertPulpOK()

    def test_06_two_roles_two_users(self):
        # create users
        self.user.create(self.pulp)
        self.assertPulpOK()
        
        self.user2.create(self.pulp)
        self.assertPulpOK()
        
        # grant permissions 
        self.role.grant_permission(self.pulp, data={"role_id": self.role.data['id'], "resource": "/", "operations": ["READ", "EXECUTE"]})
        self.role.grant_permission(self.pulp, data={"role_id": self.role.data['id'], "resource": "/repositories/", "operations": ["READ", "EXECUTE"]})
        self.assertPulpOK()
        
        self.role2.grant_permission(self.pulp, data={"role_id": self.role2.data['id'], "resource": "/", "operations": ["READ", "EXECUTE"]})
        self.role2.grant_permission(self.pulp, data={"role_id": self.role2.data['id'], "resource": "/repositories/", "operations": ["READ", "EXECUTE"]})
        self.assertPulpOK()

        # add users to roles
        self.role.add_user(
            self.pulp,
            data={'login': self.user.data['login']}
        )
        self.assertPulp(code=200)
        
        self.role2.add_user(
            self.pulp,
            data={'login': self.user.data['login']}
        )
        self.assertPulp(code=200)
        
        self.role2.add_user(
            self.pulp,
            data={'login': self.user2.data['login']}
        )
        self.assertPulp(code=200)
        
        # check users' permissions
        with self.user_pulp.asserting(True):
            Repo.list(self.user_pulp)

        with self.user_pulp2.asserting(True):
            Repo.list(self.user_pulp2)
        
        # revoke permissions from role2
        self.role2.revoke_permission(self.pulp, data={"role_id": self.role2.data['id'], "resource": "/", "operations": ["READ", "EXECUTE"]})
        self.role2.revoke_permission(self.pulp, data={"role_id": self.role2.data['id'], "resource": "/repositories/", "operations": ["READ", "EXECUTE"]})
        self.assertPulpOK()
        
        # check users' permissions
        with self.user_pulp.asserting(True):
            Repo.list(self.user_pulp)
            
        with self.assertRaises(AssertionError):
            with self.user_pulp2.asserting(True):
                Repo.list(self.user_pulp2)
        
