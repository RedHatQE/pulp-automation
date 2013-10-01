import item, json, namespace
from pulp import Request

class Repo(item.Item):
    path = '/repositories/'
    relevant_data_keys = ['id', 'display_name', 'description', 'notes']
    required_data_keys = ['id']


class Importer(item.Item):
    path = '/importers/'
    relevant_data_keys = ['importer_type_id', 'importer_config']
    required_data_keys = ['importer_type_id']

    @property
    def id(self):
        '''id is an alias for self.data['importer_type_id']'''
        return self.data['importer_type_id']

    @id.setter
    def id(self, other):
        '''id is an alias for self.data['importer_type_id']'''
        self.data['importer_type_id'] = other


class YumImporter(Importer):

    def __init__(self, data={'importer_type_id': 'yum_importer', 'importer_config': {'feed': None}}):
        super(YumImporter, self).__init__(data)

    @property
    def feed(self):
        try:
            return self.data['importer_config']['feed']
        except KeyError:
            return None

    @feed.setter
    def feed(self, other):
        if 'importer_config' not in self.data:
            self.data['importer_config'] = {}
        self.data['importer_config']['feed'] = other
