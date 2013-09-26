import item
from . import path as pulp_path
from requests import Request


class Repo(item.Item):
    path = pulp_path + '/repositories/'
    headers = {'Content-Type': 'application/json'}

    def assert_data(self, data):
        assert 'id' in data and data['id'] is not None, "no id field in data %s" % data
        
    def create(self):
        return self.request('POST', self.path, data=self.json_data)

    def delete(self):
        return self.request('DELETE', self.path + "/" + self.data['id'] + "/") 
