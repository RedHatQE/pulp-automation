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

    def associate_distributor(
        self,
        pulp,
        data,
        path='/distributors/'
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
        
    def list_distributors(
        self,
        pulp,
    ):
        path = path_join(self.path, self.id, Distributor.path)
        with pulp.asserting(True):
            response = pulp.send(self.request('GET', path=path)).json()
        return map(lambda x: Distributor(data=x, path_prefix=path_join(self.path, self.id)), response)

    def get_importer(
        self,
        pulp,
        id,
    ):
        path = path_join(self.path, self.id, Importer.path)
        with pulp.asserting(True):
            return Importer.from_response(pulp.send(self.request('GET', path=path)))
            
    def get_distributor(
        self,
        pulp,
        id,
    ):
        path = path_join(self.path, self.id, Distributor.path)
        with pulp.asserting(True):
            return Distributor.from_response(pulp.send(self.request('GET', path=path)))
        


class Importer(item.AssociatedItem):
    path = '/importers/'
    relevant_data_keys = ['id', 'importer_type_id', 'repo_id', 'config', 'last_sync']
    
class Distributor(item.AssociatedItem):
    path = '/distributors/'
    relevant_data_keys = ['id', 'distributor_type_id', 'repo_id', 'config', 'last_publish', 'auto_publish']


SAMPLE_YUM_DISTRIBUTOR_CONFIG_DATA = {
    "distributor_id": "yum_distributor",
    "auto_publish": True,
    "distributor_type": "yum_distributor",
    "distributor_config": {
        "http": False,
        "https": True,
        "relative_url": "/repos/pulp/pulp/demo_repos/zoo/"
    }
}

SAMPLE_EXPORT_DISTRIBUTOR_CONFIG_DATA = {
    "distributor_id": "export_distributor",
    "auto_publish": False,
    "distributor_type": "export_distributor",
    "distributor_config":{
        "http": False,
        "https": True
    }
}

SAMPLE_YUM_DISTRIBUTOR_DATA = {
        "_id": {
            "$oid": "5257ef5cc805d066faef1d2f"
        },
        "_ns": "repo_distributors",
        "auto_publish": True,
        "config": {
            "http": False,
            "https": True,
            "relative_url": "/repos/pulp/pulp/demo_repos/zoo/"
        },
        "distributor_type_id": "yum_distributor",
        "id": "yum_distributor",
        "last_publish": "2013-10-11T13:06:32Z",
        "repo_id": "test_rpm_repo",
        "scheduled_publishes": [],
        "scratchpad": {}
}

SAMPLE_EXPORT_DISTRIBUTOR_DATA = {
        "_id": {
            "$oid": "5257ef5cc805d066faef1d30"
        },
        "_ns": "repo_distributors",
        "auto_publish": False,
        "config": {
            "http": False,
            "https": True
        },
        "distributor_type_id": "export_distributor",
        "id": "export_distributor",
        "last_publish": None,
        "repo_id": "test_rpm_repo",
        "scheduled_publishes": [],
        "scratchpad": None
}
