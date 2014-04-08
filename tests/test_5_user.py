import pulp_test, json
from pulp_auto.user import User
from pulp_auto import login, Pulp, format_response, format_preprequest


def setUpModule():
    pass


class UserTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(UserTest, cls).setUpClass()
        cls.user = User(data={"login": cls.__name__ + "_user", "name": cls.__name__, "password": cls.__name__, 'roles': []})
        cls.user1 = User(data={"login": cls.__name__ + "_user", "name": 'myuser', "password": 'myuser', 'roles': []})
        cls.user2 = User(data={"login": 'testuser', "name": 'testuser', "password": 'testuser', 'roles': []})
        cls.user3 = User(data={"login": 'super', "name": 'user', "password": 'user', 'roles': []})
        cls.user4 = User(data={"login": 'admin', "name": 'admin', "password": 'admin', 'roles': []})
        # a new session has to be created for the user as auth credeantials of admin are used by default
        cls.user_pulp = Pulp(cls.pulp.url, auth=(cls.user.data['login'], cls.user.data['password']))


class SimpleUserTest(UserTest):

    def test_01_create_user(self):
        self.user.create(self.pulp)
        self.assertPulpOK()

    def test_02_no_dupl_user(self):
        # check that you cannot create user with same login
        self.user1.create(self.pulp)
        self.assertPulp(code=409)

    def test_03_get_user(self):
        user = User.get(self.pulp, self.user.id)
        self.assertEqual(self.user, user)

    def test_04_get_unexistant_user(self):
        with self.assertRaises(AssertionError):
            User.get(self.pulp, 'some_id')
        self.assertPulp(code=404)

    def test_05_list_users(self):
        users = User.list(self.pulp)
        self.assertIn(self.user, users)

    def test_06_search_user(self):
        user = User.search(self.pulp, data={"criteria": {"fields": ["login", "roles"], "filters": {'login': 'admin'}}})
        self.assertIn(User({'login': 'admin'}, ['login'], ['login']), user)

    def test_07_search_unexostant_user(self):
        user = User.search(self.pulp, data={"criteria": {"fields": ["login", "roles"], "filters": {'login': 'unexistant_user'}}})
        self.assertEqual([], user)

    def test_08_check_super_user_created(self):
        #check that a super user can be created
        self.user3.create(self.pulp)
        self.assertPulpOK()
        self.user3 |= {"roles": ['super-users']}
        self.user3.delta_update(self.pulp)
        self.assertPulp(code=200)

    def test_09_search_super_user(self):
        user = User.search(self.pulp, data={"criteria": {"fields": ["login", "roles"], "filters": {'roles': 'super-users'}}})
        # we have already 2 super users
        self.assertEqual(len(user), 2)

    def test_10_update_user(self):
        name = 'name %s' % self.__class__.__name__
        self.user |= {'name': name}
        self.user.delta_update(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(User.get(self.pulp, self.user.id).data['name'], name)

    def test_11_update_unexistant_user(self):
        name = 'name %s' % self.__class__.__name__
        self.user2 |= {'name': name}
        with self.assertRaises(AssertionError):
            self.user2.delta_update(self.pulp)
        self.assertPulp(code=404)

    def test_12_update_password_user(self):
        password = 'password'
        self.user.data["password"] = password
        self.user.delta_update(self.pulp)
        self.assertPulp(code=200)
        # checking if user cannot login with old password
        with self.assertRaises(AssertionError):
            with self.user_pulp.asserting(True):
                self.user_pulp.send(login.request())
        #checking if the user can login with new password
        self.user_pulp.auth = (self.user.data['login'], password)
        # self.assertPulpOK() cannot be used here, as we have to check response from user session, not admin session
        with self.user_pulp.asserting(True):
            self.user_pulp.send(login.request())
        # FIXME the password is not restored to the default one

    def test_13_delete_users(self):
        self.user.delete(self.pulp)
        self.assertPulpOK()
        #check you cannot delete twice the user
        self.user.delete(self.pulp)
        self.assertPulp(code=404)
        #check you can delete a super user in case it is not the last one
        self.user3.delete(self.pulp)
        self.assertPulpOK()
        #check you cannot delete last super user
        self.user4.delete(self.pulp)
        self.assertPulp(code=400)

    def test_14_check_users_deleted(self):
        #check that deletion was successful
        users = User.list(self.pulp)
        # there should be ony 1 user, in our case admin
        self.assertEqual(1, len(users))
