import namespace, json, requests
from . import (path as pulp_path, normalize_url, path_join)
from pulp import Request, format_response
from hasdata import HasData


class Item(HasData):
    '''a generic pulp rest api item'''
    path = pulp_path
    headers = {'Content-Type': 'application/json'}
    relevant_data_keys = ['id']
    required_data_keys = ['id']

    @classmethod
    def get(cls, pulp, id, path_prefix=''):
        '''create an instance from pulp id'''
        response = pulp.send(Request('GET', path_prefix + "/" + cls.path + "/" + id + "/"))
        assert pulp.is_ok, "non-ok response:\n %s" % format_response(response)
        return cls(response.json())

    @classmethod
    def list(cls, pulp, path_prefix=''):
        '''create a list of instances from pulp'''
        response = pulp.send(Request('GET', path_prefix + "/" + cls.path))
        assert pulp.is_ok, "non-ok response:\n%s" % format_response(response)
        return map (lambda x: cls(data=x), response.json())

    @property
    def id(self):
        '''shortcut for self.data['id']; all items should give one'''
        return self.data['id']

    @id.setter
    def id(self, other):
        self.data['id'] = other

    def reload(self, pulp, path_prefix=''):
        '''reload self.data from pulp'''
        self.data = self.get(pulp, self.id, path_prefix=path_prefix).data

    def create(self, pulp, path_prefix=''):
        '''create self in pulp'''
        return pulp.send(Request('POST', path_prefix + "/" + self.path, data=self.json_data, headers=self.headers))

    def delete(self, pulp, path_prefix=''):
        '''remove self from pulp'''
        return pulp.send(Request('DELETE', path_prefix + "/" + self.path + "/" + self.id + "/"))

    def update(self, pulp, path_prefix=''):
        '''update pulp with self.data'''
        item = self.get(pulp, self.id)
        # update call requires a delta-data dict; computing one based on data differences
        # note that id shouldn't appear in the delta since the get is using it
        delta = json.dumps({
            'delta': self.delta(item)
        })
        return pulp.send(
            Request('PUT', path_prefix + "/" + self.path + "/" + self.id + "/", data=delta, headers=self.headers)
        )

    def __mul__(self, other):
        '''multiplication results in an association of items'''
        return ItemAssociation(self, other)

    def __div__(self, other):
        '''division results in an disassociation of items'''
        return ItemDisAssociation(self, other)

    def associate(self, pulp, other):
        '''handle item association'''
        return (self * other).create(pulp)
       
    def disassociate(self, pulp, other):
        '''handle item disassociation'''
        return (self / other).create(pulp)

class ItemType(HasData):
    '''A type-instance that doesn't live on its own unless associated with an Item instance
    An example: YumImporterType; one can't query /pulp/api/v2/importers/yum_importer
    '''
    path = pulp_path
    relevant_data_keys = []
    required_data_keys = []
    headers = {'Content-Type': 'application/json'}

    def create(self, pulp, path_prefix):
        return pulp.send(Request('POST', path_prefix + '/' + self.path, data=json.dumps(self.data), headers=self.headers))

    def list(self, pulp, path_prefix=''):
        '''return list of type(self.right) items based on the pulp data'''
        return map(lambda element: self.instantiate(element), pulp.send(Request('GET', path_prefix + '/' + self.path)).json())

    def get(self, pulp, path_prefix=''):
        '''return new instance of type(self.right) item based on the pulp data'''
        result = pulp.send(Request('GET', path_prefix + '/' + self.path + '/' + self.id + '/')) 
        assert pulp.is_ok, "get request not passed for: %r\n%s" % (self, format_response(result))
        return self.instantiate(result.json())

    def delete(self, pulp, path_prefix=''):
        raise TypeError("A %s instance cannot be deleted" % self.__class__.__name__)

    @property
    def id(self):
        raise NotImplementedError

    @id.setter
    def id(self, other):
        raise NotImplementedError

    def instantiate(self, data):
        return Item(data)


class ItemAssociation(object):
    '''right-associate left-item with right-item; uses right-item.data, right-item.headers'''
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return self.__class__.__name__ + "(%r, %r)" % (self.left, self.right)

    def create(self, pulp, path_prefix=''):
        '''send the creating POST request'''
        return self.right.create(pulp, path_prefix=path_join(path_prefix, self.path))

    def delete(self, pulp, path_prefix=''):
        '''send the DELETE request'''
        return self.right.delete(pulp, path_prefix=path_join(path_prefix, self.path))

    def list(self, pulp, path_prefix=''):
        '''return list of type(self.right) items based on the pulp data'''
        return self.right.list(pulp, path_prefix=path_join(path_prefix, self.path))

    def get(self, pulp, path_prefix=''):
        '''return new instance of type(self.right) item based on the pulp data'''
        return self.right.get(pulp, path_prefix=path_join(path_prefix, self.path))

    def reload(self, pulp, path_prefix=''):
        '''reload the pulp data into self.right.data'''
        return self.right.reload(pulp, path_prefix=path_join(path_prefix, self.path))

    def update(self, pulp, path_prefix=''):
        '''update pulp with self.right.data'''
        return self.right.update(pulp, path_prefix=path_join(path_prefix, self.path))

    @property
    def data(self):
        return self.right.data

    @data.setter
    def data(self, other):
        self.right.data = other

    @property
    def path(self):
        '''path == self.left.path + self.left.id'''
        return path_join(self.left.path, self.left.id)

    @property
    def id(self):
        '''id == self.right.id'''
        return self.right.id

    def associate(self, pulp, other):
        '''stack-associate other to the self.left item'''
        return self.left.associate(pulp, other)
    
    def disassociate(self, pulp, other):
        '''stack-disassociate other from self.left item'''
        return self.left.disassociate(pulp, other)

    def __mul__(self, other):
        '''stack-associate other to self.left item'''
        return self.left * other

    def __div__(self, other):
        '''stack-disassociate other from self.left item'''
        return self.left / other

    def __xor__(self, other):
        return self.right ^ other

    def __ixor__(self, other):
        self.righ ^= other

    def __or__(self, other):
        return self.right | other

    def __ior__(self, other):
        self.right |= other

    def __eq__(self, other):
        return self.right == other

    def instantiate(self, data):
        return self.right.instantiate(data)


class ItemDisAssociation(ItemAssociation):
    '''reversed item association'''
    def delete(self, pulp):
        return super(ItemDisAssociation, self).create(pulp)

    def create(self, pulp):
        return super(ItemDisAssociation, self).delete(pulp)

