import pulp_test, json
from pulp.role import Role
 
def setUpModule():
    pass

class RoleTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RoleTest, cls).setUpClass()
        
        #create role
        with cls.pulp.asserting(True):
            response = Role.create(cls.pulp, data={'role_id': cls.__name__ + "_role"})
        cls.role = Role.from_response(response)
        
    @classmethod
    def tearDown(cls):
        # delete role
        with cls.pulp.asserting(True):
            cls.role.delete(cls.pulp)

class SimpleRoleTest(RoleTest):

    def test_01_update_role(self):
        display_name = 'A %s role' % self.__class__.__name__
        self.role |= {'display_name': display_name}
        self.role.update(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(Role.get(self.pulp, self.role.id).data['display_name'], display_name)


