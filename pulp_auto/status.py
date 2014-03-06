import item, json
from pulp_auto import (Request, )
from . import (path_join, format_response)

class Status(item.Item):
    path = '/status/'
    
    def get_status(self, pulp):
        return pulp.send(self.request('GET'))
