import item, json
from pulp_auto import (Request, )
from . import (path_join, format_response)

class RepoGroup(item.Item):
    path = '/repo_groups/'
    relevant_data_keys = ['id', 'display_name', 'description', 'repo_ids', 'notes']
    
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

    def associate_distributor(
        self,
        pulp,
        data,
        path='/distributors/'
    ):
        return pulp.send(self.request('POST', path=path, data=data))

    def get_distributor(
        self,
        pulp,
        id,
    ):
        path = path_join(GroupDistributor.path, id)
        with pulp.asserting(True):
            return GroupDistributor.from_response(pulp.send(self.request('GET', path=path)))


    def list_distributors(
        self,
        pulp,
    ):
        path = GroupDistributor.path
        with pulp.asserting(True):
            return pulp.send(self.request('GET', path=path)).json()

    def publish(
        self,
        pulp,
        distributor_group_id,
        config = None,
        path='/actions/publish/'
    ):
        data={
            'id': distributor_group_id,
            'override_config': config
        }
        return pulp.send(self.request('POST', path=path, data=data))


class GroupDistributor(item.AssociatedItem):
    path = '/distributors/'
    relevant_data_keys = ['id', 'distributor_type_id', 'repo_group_id', 'config', 'last_publish']

