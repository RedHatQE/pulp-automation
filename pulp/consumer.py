import item, json
from pulp import (Request, )
from . import (path_join, format_response)

class Consumer(item.Item):
    relevant_data_keys = ['id', 'display_name', 'description', 'notes']
    path='/consumers/'
