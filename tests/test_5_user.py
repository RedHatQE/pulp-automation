import pulp_test, json
from pulp_auto.user import User 
from pulp_auto import login, Pulp, format_response, format_preprequest


def setUpModule():
    pass


class UserTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(UserTest, cls).setUpClass()
        cls.user = User(data={"login": cls.__name__ + "_user", "name": cls.__name__, "password": cls.__name__})
        # a new session has to be created for the user as auth credeantials of admin are used by default
        cls.user_pulp = Pulp(cls.pulp.url, auth=(cls.user.data['login'], cls.user.data['password']))


class SimpleUserTest(UserTest):

    def test_01_create_user(self):
        self.user.create(self.pulp)
        self.assertPulpOK()

    def test_02_get_user(self):
        user = User.get(self.pulp, self.user.id)
        self.assertEqual(self.user, user)

    def test_03_list_users(self):
        users = User.list(self.pulp)
        self.assertIn(self.user, users)

    def test_04_update_user(self):
        name = 'name %s' % self.__class__.__name__
        self.user |= {'name': name}
        self.user.update(self.pulp)
        self.assertPulp(code=200)
        self.assertEqual(User.get(self.pulp, self.user.id).data['name'], name)

    def test_05_update_password_user(self):
        password = 'password'
        self.user.data["password"] = password
        self.user.update(self.pulp)
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

    def test_06_delete_user(self):
        self.user.delete(self.pulp)
        self.assertPulpOK()
