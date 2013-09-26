import namespace, json, requests
from . import (path as pulp_path, normalize_url)

class Item(object):
    def __init__(self, data={}):
        self.data = data

    def __str__(self):
        return str(self.data)

    def __repr__(self, path):
        return self.__class__.__name__ + "(%s)" % repr(self.data)

    def request(self, method, path, data=None, headers=None):
        '''create a callable request compatible with pulp.send''' 
        return lambda url, auth: \
            requests.Request(
                method,
                normalize_url(url + path),
                auth=auth,
                data=data,
                headers=headers
            ).prepare()
 
    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, _data):
        self.assert_data(_data)
        self._data = _data

    @property
    def json_data(self):
        return json.dumps(self.data)
