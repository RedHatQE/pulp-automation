import json

class HasData(object):
    required_data_keys = [] # keys that are asserted and not touched by data update
    relevant_data_keys = [] # keys relevant for comparison of values

    def assert_data(self, data):
        for key in self.required_data_keys:
            assert key in data and data[key] is not None, "no %s key in data %s" % (key, data)

    def __init__(self, data={}):
        self.data = data

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return self.__class__.__name__ + "(%r)" % self.data

    def __eq__(self, other):
        '''compare items based on self.relevant_data_keys in data'''
        if hasattr(other, 'data'):
            data = other.data
        else:
            data = other
        try:
            return reduce(
                lambda x, y: x and (y[0] == y[1]), \
                    [(self.data[key], data[key]) for key in self.relevant_data_keys],
                    True
            )
        except KeyError:
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

    def delta(self, other):
        '''return the difference between the data'''
        if hasattr(other, 'data'):
            data = other.data
        else:
            data = other
        return {
            key: self.data[key] for key in filter( \
                lambda key: data[key] != self.data[key], \
                    self.relevant_data_keys
            )
        }

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

