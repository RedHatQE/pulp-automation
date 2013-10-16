import item, json
from pulp import (Request, )
from . import (path_join, format_response)

class User(item.Item):
    relevant_data_keys = ['login', 'name', 'password']
    required_data_keys = ['login']
    path='/users/'

    @property
    def id(self):
        return self.data['login']

    @id.setter
    def id(self, other):
        self.data['login'] = other

