import item, json
from pulp import (Request, )
from . import (path_join, format_response)


class User(item.Item):
    relevant_data_keys = ['login', 'name']
    required_data_keys = ['login']
    path = '/users/'

    @property
    def id(self):
        return self.data['login']

    @id.setter
    def id(self, other):
        self.data['login'] = other

    def update(self, pulp):
        item = self.get(pulp, self.id)
        # update call requires a delta-data dict; computing one based on data differences
        # note that id shouldn't appear in the delta since the get is using it
        delta = {
            'delta': self.delta(item)
        }

        if 'password' in self.data:
            # password has to be updated all the time
            delta['delta']['password'] = self.data['password']

        return pulp.send(
            self.request('PUT', data=delta)
        )
