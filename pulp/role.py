import item, json
from pulp import (Request, )
from . import (path_join, format_response)

class Role(item.Item):
    relevant_data_keys = ['id', 'display_name', 'description']
    path='/roles/'

    @classmethod
    def create(cls, pulp, data):
        return pulp.send(Request('POST', path=cls.path, data=data))
