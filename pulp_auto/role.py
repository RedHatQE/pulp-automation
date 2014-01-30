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

    def grant_permission(
        self,
        pulp,
        data,
        path='/actions/grant_to_role/'
    ):
        return pulp.send(Request('POST', data=data, path=path_join(Permission.path, path)))

    def revoke_permission(
        self,
        pulp,
        data,
        path='/actions/revoke_from_role/'
    ):
        return pulp.send(Request('POST', data=data, path=path_join(Permission.path, path)))


class User(item.AssociatedItem):
    path = '/users/'
