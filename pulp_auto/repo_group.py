import item, json
from pulp_auto import (Request, )
from . import (path_join, format_response)

class RepoGroup(item.Item):
    path = '/repo_groups/'
    relevant_data_keys = ['id', 'display_name', 'description', 'repo_ids', 'notes']

    def update(self, pulp, data):
        item = self.get(pulp, self.id)
        return pulp.send(self.request('PUT', data=data))
    
    def associate_repo(
        self,
        pulp,
        data={
            'criteria': {
            }
        },
        path='/actions/associate/'
    ):
        print 
        return pulp.send(self.request('POST', path=path, data=data))
        
    def unassociate_repo(
        self,
        pulp,
        data={
            'criteria': {
            }
        },
        path='/actions/unassociate/'
    ):
        return pulp.send(self.request('POST', path=path, data=data))
