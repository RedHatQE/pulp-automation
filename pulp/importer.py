import item

class Importer(item.Item):
    path = '/importers/'
    relevant_data_keys = ['config', 'importer_type_id', 'repo_id']
    required_data_keys = ['id']

class ImporterType(item.ItemType):
    path = '/importers/'
    relevant_data_keys = ['importer_type_id', 'importer_config']
    required_data_keys = ['importer_type_id']

    def instantiate(self, data):
        return Importer(data=data)

    @property
    def id(self):
        '''id is an alias for self.data['importer_type_id']'''
        return self.data['importer_type_id']

    @id.setter
    def id(self, other):
        '''id is an alias for self.data['importer_type_id']'''
        self.data['importer_type_id'] = other

    @property
    def importer_config(self):
        return self.data['importer_config']

    @importer_config.setter
    def importer_config(self, other):
        self.data['importer_config'] = other

class Importer(item.Item):
    path = '/importers/'
    relevant_data_keys = ['config', 'importer_type_id', 'repo_id']
    required_data_keys = ['id']


# "constants"/globals importer data
YUM = {
    'id': 'yum_importer',
    'config': {
        'feed': None
    },
    'importer_type_id': 'yum_importer',
    'repo_id': None
}

YUM_TYPE = {
    'importer_type_id': 'yum_importer',
    'importer_config': {
        'feed': None
    }
}
