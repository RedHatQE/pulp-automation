import item, json
from pulp_auto import (Request, path_join)


class Permission(item.Item):
    relevant_data_keys = ['resource', 'users']
    required_data_keys = ['resource']
    path = '/permissions/'

    @property
    def id(self):
        return self.data['resource']

    @id.setter
    def id(self, other):
        self.data['resource'] = other

    def create(self, pulp):
        raise TypeError('Cannot create new permissions. Valid permissions are [CREATE, READ, UPDATE, DELETE, EXECUTE]')

    def delete(self, pulp):
        raise TypeError('Cannot create new permissions. Valid permissions are [CREATE, READ, UPDATE, DELETE, EXECUTE]')

    def update(self, pulp):
        raise TypeError('Cannot create new permissions. Valid permissions are [CREATE, READ, UPDATE, DELETE, EXECUTE]')
