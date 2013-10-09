import item, json
from pulp import (Request, )
from . import (path_join, format_response)

class Repo(item.Item):
    relevant_data_keys = ['id', 'display_name', 'description', 'notes']
    path='/repositories/'

    def associate_importer(
        self,
        pulp,
        data,
        path='/importers/'
    ):
        return pulp.send(self.request('POST', path=path, data=data))

    def sync(
        self,
        pulp,
        data={
            'override_config': {
            }
        },
        path='/actions/sync/'
    ):
        return pulp.send(self.request('POST', path=path, data=data))

    def list_importers(
        self,
        pulp,
    ):
        path = path_join(self.path, self.id, Importer.path)
        with pulp.asserting(True):
            response = pulp.send(self.request('GET', path=path)).json()
        return map(lambda x: Importer(data=x, path_prefix=path_join(self.path, self.id)), response)

    def get_importer(
        self,
        pulp,
        id,
    ):
        path = path_join(self.path, self.id, Importer.path)
        with pulp.asserting(True):
            return Importer.from_response(pulp.send(self.request('GET', path=path)))
        


class Importer(item.AssociatedItem):
    path = '/importers/'
    relevant_data_keys = ['id', 'importer_type_id', 'repo_id', 'config', 'last_sync']

