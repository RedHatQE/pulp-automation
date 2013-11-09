import pulp_test, json
from pulp_auto.role import Role 
from pulp_auto.user import User 
 
def setUpModule():
    pass

class RoleTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RoleTest, cls).setUpClass()
        
        # create roles
        with cls.pulp.asserting(True):
            response = Role.create(cls.pulp, data={'role_id': cls.__name__ + "_role"})
        cls.role = Role.from_response(response)
        
        with cls.pulp.asserting(True):
            response2 = Role.create(cls.pulp, data={'role_id': cls.__name__ + "_role2"})
        cls.role2 = Role.from_response(response2)
        
        # users
        cls.user = User(data={"login": cls.__name__ + "_user", "name": cls.__name__, "password": cls.__name__})
        cls.user2 = User(data={"login": cls.__name__ + "_user2", "name": cls.__name__, "password": cls.__name__})
        
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

class SimpleRoleTest(RoleTest):
    
    def test_01_get_role(self):
        self.assertEqual(self.role, Role.get(self.pulp, self.role.id))
        self.assertEqual(self.role2, Role.get(self.pulp, self.role2.id))

    def test_02_list_roles(self):
        self.assertIn(self.role, Role.list(self.pulp))
        self.assertIn(self.role2, Role.list(self.pulp))

    def test_03_update_role(self):
        display_name = 'A %s role' % self.__class__.__name__
        self.role |= {'display_name': display_name}
        self.role.update(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(Role.get(self.pulp, self.role.id).data['display_name'], display_name)
        
    def test_04_add_user(self):
        # create user
        self.user.create(self.pulp)
        self.assertPulpOK()
        
        # add user to the role
        self.role.add_user(
            self.pulp,
            data={'login': self.user.data['login']}
        )
        self.assertPulp(code=200)
        self.assertEqual(Role.get(self.pulp, self.role.id).data['users'], [self.user.data['login']])
        
    def test_05_remove_user(self):
        # remove user from the role
        self.role.remove_user(
            self.pulp,
            self.user.data['login']
        )
        self.assertPulp(code=200)
        self.assertEqual(Role.get(self.pulp, self.role.id).data['users'], [])
        
    def test_06_add_2_users(self):
        # create second user
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
        self.assertEqual(Role.get(self.pulp, self.role.id).data['users'], [self.user.data['login'], self.user2.data['login']])
        

