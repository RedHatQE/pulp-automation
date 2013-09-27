import namespace, json, requests
from . import (path as pulp_path, normalize_url)
from pulp import Request

class Item(object):
    '''a generic pulp rest api item'''
    path = pulp_path
    headers = {'Content-Type': 'application/json'}
    relevant_data_keys = ['id']
    required_data_keys = ['id']

    def assert_data(self, data):
        for key in self.required_data_keys:
            assert key in data and data[key] is not None, "no %s key in data %s" % (key, data)

    def __init__(self, data={}):
        self.assert_data(data)
        self.data = data

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return self.__class__.__name__ + "(%r)" % self.data

    def __eq__(self, other):
        '''compare items based on relevant keys in data'''
        try:
            # assert same relevant keys
            if self.relevant_data_keys != other.relevant_data_keys:
                return False

            return reduce(
                lambda x, y: x and (y[0] == y[1]), \
                    [(self.data[key], other.data[key]) for key in self.relevant_data_keys],
                    True
            )
        except KeyError, AttributeError:
            return False

    @classmethod
    def get(cls, pulp, id):
        '''create an instance from pulp id'''
        response = pulp.send(Request('GET', cls.path + "/" + id + "/"))
        assert pulp.is_ok, "non-ok response: %s" % response.text
        return cls(response.json())

    @classmethod
    def list(cls, pulp):
        '''create a list of instances from pulp'''
        response = pulp.send(Request('GET', cls.path))
        assert pulp.is_ok, "non-ok response: %s" % response.text
        return map (lambda x: cls(data=x), response.json())

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

    def reload(self, pulp):
        '''reload self.data from pulp'''
        self.data = self.get(pulp, self.data['id']).data

    def create(self, pulp):
        '''create self in pulp'''
        return pulp.send(Request('POST', self.path, data=self.json_data, headers=self.headers))

    def delete(self, pulp):
        '''remove self from pulp'''
        return pulp.send(Request('DELETE', self.path + "/" + self.data['id'] + "/"))

    def update(self, pulp):
        '''update pulp with self.data'''
        item = self.get(pulp, self.data['id'])
        # update call requires a delta-data dict; computing one based on data differences
        # note that id shouldn't appear in the delta since the get is using it
        delta = json.dumps({
            'delta': {
                key: self.data[key] for key in filter( \
                        lambda key: item.data[key] != self.data[key], \
                        self.relevant_data_keys
                )
            }
        })
        return pulp.send(
            Request('PUT', self.path + "/" + self.data['id'] + "/", data=delta, headers=self.headers)
        )

