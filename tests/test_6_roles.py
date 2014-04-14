import pulp_test, json
from pulp_auto import Pulp
from pulp_auto.role import Role
from pulp_auto.user import User
from pulp_auto.repo import Repo


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

        with cls.pulp.asserting(True):
            response3 = Role.create(cls.pulp, data={'role_id': cls.__name__ + "_role3"})
        cls.role3 = Role.from_response(response3)

        # users
        cls.user = User(data={"login": cls.__name__ + "_user", "name": cls.__name__, "password": cls.__name__})
        cls.user2 = User(data={"login": cls.__name__ + "_user2", "name": cls.__name__, "password": cls.__name__})
        # a new session has to be created for the user as auth credeantials of admin are used by default
        cls.user_pulp = Pulp(cls.pulp.url, auth=(cls.user.data['login'], cls.user.data['password']))
        cls.user_pulp2 = Pulp(cls.pulp.url, auth=(cls.user2.data['login'], cls.user2.data['password']))

    @classmethod
    def tearDownClass(cls):
        # delete users
        with cls.pulp.asserting(True):
            cls.user.delete(cls.pulp)
        with cls.pulp.asserting(True):
            cls.user2.delete(cls.pulp)

        # delete roles
        with cls.pulp.asserting(True):
            cls.role2.delete(cls.pulp)


class SimpleRoleTest(RoleTest):

    def test_01_no_dupl_role(self):
        Role.create(self.pulp, data={'role_id': self.role.id})
        self.assertPulp(code=409)

    def test_02_get_role(self):
        self.assertEqual(self.role, Role.get(self.pulp, self.role.id))
        self.assertEqual(self.role2, Role.get(self.pulp, self.role2.id))

    def test_03_get_unexistant_role(self):
        with self.assertRaises(AssertionError):
            Role.get(self.pulp, 'some_id')
        self.assertPulp(code=404)

    def test_04_list_roles(self):
        self.assertIn(self.role, Role.list(self.pulp))
        self.assertIn(self.role2, Role.list(self.pulp))

    def test_05_update_role(self):
        display_name = 'A %s role' % self.__class__.__name__
        self.role |= {'display_name': display_name}
        self.role.delta_update(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(Role.get(self.pulp, self.role.id).data['display_name'], display_name)

    def test_05_update_role_permission_bz1066040(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1066040 
        self.role.data["permissions"] = {"/":["CREATE","DELETE"]}
        self.role.delta_update(self.pulp)
        self.assertPulp(code=400)

    def test_06_update_unexistant_role(self):
        self.role3.delete(self.pulp)
        display_name = 'A %s role' % self.__class__.__name__
        self.role3 |= {'display_name': display_name}
        with self.assertRaises(AssertionError):
            self.role3.delta_update(self.pulp)
        self.assertPulp(code=404)

    def test_07_add_user(self):
        # create user
        self.user.create(self.pulp)
        self.assertPulpOK()

        # add user to the role
        self.role.add_user(
            self.pulp,
            self.user.id
        )
        self.assertPulp(code=200)
        self.assertEqual(Role.get(self.pulp, self.role.id).data['users'], [self.user.id])

    def test_08_add_unexistant_user(self):
        # add user to the role
        self.role.add_user(
            self.pulp,
            "Unexistant_user"
        )
        self.assertPulp(code=404)

    def test_09_remove_user(self):
        # remove user from the role
        self.role.remove_user(
            self.pulp,
            self.user.id
        )
        self.assertPulp(code=200)
        self.assertEqual(Role.get(self.pulp, self.role.id).data['users'], [])

    def test_10_add_2_users(self):
        # create second user
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
        self.assertEqual(Role.get(self.pulp, self.role.id).data['users'], [self.user.id, self.user2.id])

    def test_11_add_role_perm(self):
        self.role.grant_permission(self.pulp, self.role.id, "/", ["READ", "EXECUTE"])
        self.role.grant_permission(self.pulp, self.role.id, "/repositories/", ["READ", "EXECUTE"])
        self.assertPulpOK()

    def test_12_check_user_perm(self):
        with self.user_pulp.asserting(True):
            Repo.list(self.user_pulp)

        with self.user_pulp2.asserting(True):
            Repo.list(self.user_pulp2)

    def test_13_remove_user(self):
        # remove user from the role
        self.role.remove_user(
            self.pulp,
            self.user2.id
        )
        self.assertPulp(code=200)

    def test_14_check_bindings_removed(self):
        #check that after user2 removal from role user binding are also removed
        with self.assertRaises(AssertionError):
            with self.user_pulp2.asserting(True):
                Repo.list(self.user_pulp2)

    def test_15_check_bindings_removed(self):
        self.role.delete(self.pulp)
        self.assertPulpOK()
        #check that after role deletion user binding are also removed
        with self.assertRaises(AssertionError):
            with self.user_pulp.asserting(True):
                Repo.list(self.user_pulp)

    def test_16_delete_unexistant_role(self):
        #check you cannot delete role twice
        self.role.delete(self.pulp)
        self.assertPulp(code=404)
