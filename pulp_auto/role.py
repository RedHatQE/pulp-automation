import item, json
from pulp_auto import (Request, )
from . import (path_join, format_response)
from permission import Permission


class Role(item.Item):
    relevant_data_keys = ['id', 'display_name', 'description']
    path = '/roles/'

    @classmethod
    def create(cls, pulp, data):
        return pulp.send(Request('POST', path=cls.path, data=data))

    def add_user(
        self,
        pulp,
        login,
        path='/users/'
    ):
        data = {
            "login": login
        }
        return pulp.send(self.request('POST', path=path, data=data))

    def remove_user(
        self,
        pulp,
        user_id,
    ):
        path = path_join(User.path, user_id)
        return pulp.send(self.request('DELETE', path=path))

    def grant_permission(
        self,
        pulp,
        role_id,
        resource,
        operations,
        path='/actions/grant_to_role/'
    ):
        data = {
            "role_id": role_id,
            "resource": resource, 
            "operations": operations
        }
        return pulp.send(Request('POST', data=data, path=path_join(Permission.path, path)))

    def revoke_permission(
        self,
        pulp,
        role_id,
        resource,
        operations,
        path='/actions/revoke_from_role/'
    ):
        data = {
            "role_id": role_id,
            "resource": resource, 
            "operations": operations
        }
        return pulp.send(Request('POST', data=data, path=path_join(Permission.path, path)))


class User(item.AssociatedItem):
    path = '/users/'
