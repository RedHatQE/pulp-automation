import item, json
from pulp_auto import (Request, )
from . import (path_join, format_response)

class ConsumerGroup(item.Item):
    path = '/consumer_groups/'
    relevant_data_keys = ['id', 'display_name', 'description', 'consumer_ids', 'notes']

    def update(self, pulp, data):
        item = self.get(pulp, self.id)
        return pulp.send(self.request('PUT', data=data))
