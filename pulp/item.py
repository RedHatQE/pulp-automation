import namespace, json, requests
from . import (path as pulp_path, normalize_url)
from pulp import Request, format_response

class HasData(object):
    required_data_keys = []
    relevant_data_keys = []

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

    def data_add(self, other_data):
        '''add other_data items save for keys in required_data_keys'''
        data = self.data.copy()
        data.update(filter(lambda (k, v): k not in self.required_data_keys, other_data.items()))
        return data

    def data_subtract(self, other_data):
        '''subtract other_data items save for keys in required_data_keys'''
        data = self.data.copy()
        items = filter(lambda (k, v): k not in self.required_data_keys and k in data, other_data.items())
        for k, v in items:
            del(data[k])
        return data

    def __or__(self, other):
        '''call to create a new Item with data set to union self.dict and other.dict
        That is save for self.required_data_keys'''
        if hasattr(other, 'data'):
            data = self.data_add(other.data)
        else:
            data = self.data_add(other)

        return type(self)(data=data)

    def __ior__(self, other):
        '''call to update self.data with other.data'''
        if hasattr(other, 'data'):
            data = self.data_add(other.data)
        else:    
            data = self.data_add(other)

        self.data = data
        return self

    def __xor__(self, other):
        '''call to remove keys found in both self and other
        That is save for self.required_data_keys'''
        if hasattr(other, 'data'):
            data = self.data_subtract(other.data)
        else:
            data = self.data_subtract(other)

        return type(self)(data=data)

    def __ixor__(self, other):
        '''call to remove keys found in both self and other
        That is save for self.required_data_keys'''
        if hasattr(other, 'data'):
            data = self.data_subtract(other.data)
        else:
            data = self.data_subtract(other)

        self.data = data
        return self

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
        assert pulp.is_ok, "non-ok response: %s" % response.text
        return cls(response.json())

    @classmethod
    def list(cls, pulp):
        '''create a list of instances from pulp'''
        response = pulp.send(Request('GET', cls.path))
        assert pulp.is_ok, "non-ok response: %s" % response.text
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
            'delta': {
                key: self.data[key] for key in filter( \
                        lambda key: item.data[key] != self.data[key], \
                        self.relevant_data_keys
                )
            }
        })
        return pulp.send(
            Request('PUT', self.path + "/" + self.id + "/", data=delta, headers=self.headers)
        )

    def __mul__(self, other):
        '''multiplication results in an association of items'''
        return ItemAssociation(self, oter)

    def __div__(self, other):
        '''division results in an disassociation of items'''
        return ItemDisAssociation(self, other)

    def associate(self, pulp, other):
        '''handle item association'''
        return (self * other).create(pulp)
       
    def disassociate(self, pulp, other):
        '''handle item disassociation'''
        return (self / other).create(pulp)

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
        headers = self.right.headers.copy()
        data = self.right.data.copy()
        return pulp.send(Request('POST', path=self.path, headers=headers, data=json.dumps(data)))

    def delete(self, pulp):
        '''send the DELETE request'''
        return pulp.send(Request('DELETE', self.path + '/' + self.id + '/'))

    def list(self, pulp):
        '''return list of type(self.right) items based on the pulp data'''
        return map(lambda element: type(self.right)(data=element), pulp.send(Request('GET', self.path)).json())

    def get(self, pulp):
        '''return new instance of type(self.right) item based on the pulp data'''
        result = pulp.send(Request('GET', self.path + '/' + self.id + '/')) 
        assert pulp.is_ok, "get request not passed for: %r\n%s" % (self, format_response(result))
        return type(self.right)(data=result.json())

    def reload(self, pulp):
        '''reload the pulp data into self.right.data'''
        right = self.get(pulp)
        self.right.data = right.data

    def update(self, pulp):
        '''update pulp with self.right.data'''
        right = self.get(pulp)
        delta = json.dumps({
            'delta': {
                key: self.right.data[key] for key in filter( \
                        lambda key: right.data[key] != self.right.data[key], \
                        self.relevant_data_keys
                )
            }
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
        '''stack-associate other to the self.right item'''
        return self.right.associate(pulp, other)
    
    def disassociate(self, pulp, other):
        '''stack-disassociate other from self.right item'''
        return self.right.disassociate(pulp, other)

    def __mul__(self, other):
        '''stack-associate other to self.right item'''
        return self.right * other

    def __div__(self, other):
        '''stack-disassociate other from self.right item'''
        return self.right / other


class ItemDisAssociation(ItemAssociation):
    '''reversed item association'''
    def delete(self, pulp):
        return super(ItemDisAssociation, self).create(pulp)

    def create(self, pulp):
        return super(ItemDisAssociation, self).delete(pulp)

