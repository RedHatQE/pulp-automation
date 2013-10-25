import item, json
from pulp import (Request, )
from . import (path_join, format_response)

class Role(item.Item):
    relevant_data_keys = ['id', 'display_name', 'description']
    path='/roles/'

    @classmethod
    def create(cls, pulp, data):
        return pulp.send(Request('POST', path=cls.path, data=data))

    def add_user(
        self,
        pulp,
        data,
        path='/users/'
    ):
        return pulp.send(self.request('POST', path=path, data=data))

    def remove_user(
        self,
        pulp,
        user_id,
    ):
        path = path_join(User.path, user_id)
        return pulp.send(self.request('DELETE', path=path))
            
    
class User(item.AssociatedItem):
    path = '/users/'
