import namespace, json, requests, logging
from . import (normalize_url, path_join, path_split, strip_url)
from pulp_auto import (Request, format_response)
from hasdata import HasData
from handler import logged
log = logging.getLogger(__name__)

class Item(HasData):
    '''a generic pulp rest api item'''
    path = '/'
    relevant_data_keys = ['id']
    required_data_keys = ['id']

    @staticmethod
    def strip_path(path):
        '''remove id and url+pulp path parts from a path'''
        return path_join(*path_split(strip_url(path))[:-1])

    @classmethod
    @logged(log.debug)
    def from_response(cls, response):
        '''basic response to Item instance conversion'''
        data = response.json()
        if isinstance(data, list):
            ret = []
            for x in data:
                ret.append(cls(data=x))
            return ret
        return cls(data=data)

    @classmethod
    @logged(log.debug)
    def from_report(cls, response):
        return response.json()

    @classmethod
    def get(cls, pulp, id, params={}):
        '''create an instance from pulp_auto id'''
        with pulp.asserting(True):
            response = pulp.send(Request('GET', path_join(cls.path, id), params=params))
        return cls.from_response(response)

    @classmethod
    def list(cls, pulp, params={}):
        '''create a list of instances from pulp_auto '''
        with pulp.asserting(True):
            response = pulp.send(Request('GET', cls.path, params=params))
        return map(lambda x: cls(data=x), response.json())

    @classmethod
    @logged(log.debug)
    def search(
        cls,
        pulp,
        data
    ):
        '''search API for various resource type as example users, repositories, consumers,etc'''
        path = '/search/'
        with pulp.asserting(True):
            '''in the data use criteria field to perform the search'''
            response = pulp.send(Request('POST', path_join(cls.path, path), data=data))
            # example of criteria search
            # {"criteria": {"sort": None, "fields": None, "limit": None, "filters": {"$and": [{"notes._repo-type": "puppet-repo"}, {"id": {"$regex": ".*repo.*"}}]}, "skip": None}}
            # {"criteria": {"sort": None, "fields": None, "limit": None, "filters": {"$and": [{"id": "m1"}, {"notes._repo-type": "puppet-repo"}]}, "skip": None}}
            # {"criteria": {"sort": None, "fields": None, "limit": None, "filters": {"$and": [{"notes._repo-type": "puppet-repo"}, {"id": {"$not": "m1"}}]}, "skip": None}}
        return cls.from_response(response)

    @property
    def id(self):
        '''shortcut for self.data['id']; all items should give one'''
        return self.data['id']

    @id.setter
    def id(self, other):
        self.data['id'] = other

    def reload(self, pulp):
        '''reload self.data from pulp_auto '''
        with pulp.asserting(True):
            self.data = type(self).from_response(pulp.send(self.request('GET'))).data

    def create(self, pulp):
        '''create self in pulp'''
        return pulp.send(Request('POST', path=self.path, data=self.data))

    def delete(self, pulp):
        '''remove self from pulp_auto '''
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

    def request(self, method, path='', data={}, params={}):
        return Request(method, data=data, path=path_join(self.path, self.id, path), params=params)


class AssociatedItem(Item):
    '''an Item that can't exist without previous association to another Item'''
    def __init__(self, path='/', data={}, **kvs):#, query=''):
        super(AssociatedItem, self).__init__(data=data, **kvs)
        # adjust path
        if '_href' in self.data:
            self.path = self.strip_path(self.data['_href'])
        else:
            # make sure there is exactly one type(self).path in the path
            self.path = path_join("/".join(path.rsplit(type(self).path)[:-1]), type(self).path)

    @classmethod
    @logged(log.debug)
    def from_response(cls, response):
        '''paht of an associated item has to be adjusted'''
        response_path = cls.strip_path(response.url)
        data = response.json()
        if isinstance(data, list):
            ret = []
            for x in data:
                ret.append(cls(data=x, path=response_path))
            return ret
        return cls(data=response.json(), path=response_path)

    @classmethod
    def get(cls, pulp, id):
        raise TypeError("can't instantiate %s from pulp_auto get response" % cls.__name__)

    @classmethod
    def list(cls, pulp):
        raise TypeError("can't instantiate %s from pulp_auto get response" % cls.__name__)


class GroupItem(Item):
    '''an Item that is bound to a Group'''
    required_data_keys = ['id', 'group_id']
    relevant_data_keys = ['id', 'group_id']

    path = '/'

    def __init__(self, data={}, group_id='', path=''):
        super(GroupItem, self).__init__(data=data)
        self.group_id = group_id
        if not path:
            self._path = type(self).path
        else:
            self._path = path

    # same path adjusting
    from_response = AssociatedItem.from_response

    @classmethod
    def get(cls, pulp, id):
        raise TypeError("can't instantiate %s from pulp_auto get response" % cls.__name__)

    @classmethod
    def list(cls, pulp):
        raise TypeError("can't instantiate %s from pulp_auto get response" % cls.__name__)

    @property
    def group_id(self):
        return self.data['group_id']

    @group_id.setter
    def group_id(self, other):
        self.data['group_id'] = other

    @property
    def path(self):
        '''concatenate type(self).path with self.group_id'''
        return path_join(self._path, self.group_id)

    @path.setter
    def path(self, other):
        '''store the last two path items as self.group_id and self._path'''
        path_items = path_split(other)
        self._path = path_join(*path_items[:-2])
        self.group_id = path_join(*path_items[-2:])
