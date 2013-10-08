import namespace, json, requests
from . import (normalize_url, path_join, path_split)
from pulp import (Request, format_response)
from hasdata import HasData


class Item(HasData):
    '''a generic pulp rest api item'''
    path = '/'
    relevant_data_keys = ['id']
    required_data_keys = ['id']

    @classmethod
    def from_response(cls, response):
        '''create an instance out of a response'''
        data = response.json()
        item = cls(data)
        # set path; strip id part
        item.path = path_join(*path_split(data['_href'])[:-1])
        return item

    @classmethod
    def get(cls, pulp, id):
        '''create an instance from pulp id'''
        response = pulp.send(Request('GET', path_join(cls.path, id)))
        assert pulp.is_ok, "non-ok response:\n %s" % format_response(response)
        return cls.from_response(response)

    @classmethod
    def list(cls, pulp):
        '''create a list of instances from pulp'''
        response = pulp.send(Request('GET', cls.path))
        assert pulp.is_ok, "non-ok response:\n%s" % format_response(response)
        return map (lambda x: cls(data=x), response.json())

    @property
    def id(self):
        '''shortcut for self.data['id']; all items should give one'''
        return self.data['id']

    @id.setter
    def id(self, other):
        self.data['id'] = other

    def reload(self, pulp):
        '''reload self.data from pulp'''
        self.data = self.get(pulp, self.id).data

    def create(self, pulp):
        '''create self in pulp'''
        return pulp.send(Request('POST', path=self.path, data=self.data))

    def delete(self, pulp):
        '''remove self from pulp'''
        return pulp.send(self.request('DELETE'))

    def update(self, pulp):
        '''update pulp with self.data'''
        item = self.get(pulp, self.id)
        # update call requires a delta-data dict; computing one based on data differences
        # note that id shouldn't appear in the delta since the get is using it
        delta = {
            'delta': self.delta(item)
        }
        return pulp.send(
            self.request('PUT', data=delta)
        )

    def request(self, method, path='', data={}):
        return Request(method, data=data, path=path_join(self.path, self.id, path))
