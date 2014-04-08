import item, json
from pulp_auto import (Request, )
from . import (path_join, format_response)

class ConsumerGroup(item.Item):
    path = '/consumer_groups/'
    relevant_data_keys = ['id', 'display_name', 'description', 'consumer_ids', 'notes']

    def associate_consumer(
        self,
        pulp,
        data={
            'criteria': {
            }
        },
        path='/actions/associate/'
    ):
        return pulp.send(self.request('POST', path=path, data=data))
        
    def unassociate_consumer(
        self,
        pulp,
        data={
            'criteria': {
            }
        },
        path='/actions/unassociate/'
    ):
        return pulp.send(self.request('POST', path=path, data=data))
