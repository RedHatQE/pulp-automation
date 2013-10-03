import namespace, json, requests
from . import (path as pulp_path, normalize_url)
from pulp import Request, format_response
from hasdata import HasData


class Item(HasData):
    '''a generic pulp rest api item'''
    path = pulp_path
    headers = {'Content-Type': 'application/json'}
    relevant_data_keys = ['id']
    required_data_keys = ['id']

    @classmethod
    def get(cls, pulp, id):
        '''create an instance from pulp id'''
        response = pulp.send(Request('GET', cls.path + "/" + id + "/"))
        assert pulp.is_ok, "non-ok response:\n %s" % format_response(response)
        return cls(response.json())

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
        return pulp.send(Request('POST', self.path, data=self.json_data, headers=self.headers))

    def delete(self, pulp):
        '''remove self from pulp'''
        return pulp.send(Request('DELETE', self.path + "/" + self.id + "/"))

    def update(self, pulp):
        '''update pulp with self.data'''
        item = self.get(pulp, self.id)
        # update call requires a delta-data dict; computing one based on data differences
        # note that id shouldn't appear in the delta since the get is using it
        delta = json.dumps({
            'delta': self.delta(item)
        })
        return pulp.send(
            Request('PUT', self.path + "/" + self.id + "/", data=delta, headers=self.headers)
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

    @property
    def id(self):
        raise NotImplementedError

    @id.setter
    def id(self, other):
        raise NotImplementedError

    def instantiate(self, data):
        return Item()

    

class ItemAssociation(HasData):
    '''right-associate left-item with right-item; uses right-item.data, right-item.headers'''
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.required_data_keys = self.right.required_data_keys
        self.relevant_data_keys = self.right.relevant_data_keys

    def __repr__(self):
        return self.__class__.__name__ + "(%r, %r)" % (self.left, self.right)

    def create(self, pulp):
        '''send the creating POST request'''
        headers = self.right.headers
        data = self.right.data
        return pulp.send(Request('POST', path=self.path, headers=headers, data=json.dumps(data)))

    def delete(self, pulp):
        '''send the DELETE request'''
        return pulp.send(Request('DELETE', self.path + '/' + self.id + '/'))

    def list(self, pulp):
        '''return list of type(self.right) items based on the pulp data'''
        return map(lambda element: self.right.instantiate(element), pulp.send(Request('GET', self.path)).json())

    def get(self, pulp):
        '''return new instance of type(self.right) item based on the pulp data'''
        result = pulp.send(Request('GET', self.path + '/' + self.id + '/')) 
        assert pulp.is_ok, "get request not passed for: %r\n%s" % (self, format_response(result))
        return self.right.instantiate(result.json())

    def reload(self, pulp):
        '''reload the pulp data into self.right.data'''
        right = self.get(pulp)
        self.right.data = right.data

    def update(self, pulp):
        '''update pulp with self.right.data'''
        right = self.get(pulp)
        delta = json.dumps({
            'delta': self.delta(right)
        })
        return pulp.send(
            Request('PUT', self.path + "/" + self.id + "/", data=delta, headers=self.headers)
        )

    @property
    def data(self):
        return self.right.data

    @data.setter
    def data(self, other):
        self.right.data = other

    @property
    def path(self):
        '''path == self.left.path + self.left.id + self.right.path'''
        return self.left.path + '/' + self.left.id + '/' + self.right.path + '/'

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


class ItemDisAssociation(ItemAssociation):
    '''reversed item association'''
    def delete(self, pulp):
        return super(ItemDisAssociation, self).create(pulp)

    def create(self, pulp):
        return super(ItemDisAssociation, self).delete(pulp)

