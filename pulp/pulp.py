import requests
from . import (normalize_url, path as pulp_path)


class Pulp(object):
    '''Pulp handle'''
    def __init__(self, url, auth=None, verify=False):
        self.session = requests.Session()
        self.url = url
        self.auth = auth
        self.verify = verify
        self.last_response = None

    def send(self, request):
        '''send a request; the request has to be callable that accepts url and auth params'''
        self.last_response = self.session.send(request(self.url, self.auth), verify=self.verify)
        return self.last_response

    @property
    def is_ok(self):
        if self.last_response is None:
            return True
        return self.last_response.status_code >= 200 and self.last_response.status_code < 400

    def call_item_method(self, item, method_name):
        '''call: item.<method_name>(self)'''
        if isinstance(item, tuple):
            # item seems to be an expression -> map method to item elements
            return tuple(map(lambda element: getattr(element, method_name)(self), item))

        return getattr(item, method_name)(self)
 

    def __lshift__(self, other):
        '''call to perform return other.create(self)'''
        return self.call_item_method(other, 'create')

    def __ilshift__(self, other):
        '''call to perform self.send(other.create(self)) , return self'''
        self.call_item_method(other, 'create')
        return self

    def __rshift__(self, other):
        '''call to perform other.delete(self)'''
        return self.call_item_method(other, 'delete')

    def __irshift__(self, other):
        '''call to perform other.delete(self), return self'''
        self.call_item_method(other, 'delete')
        return self

    def __lt__(self, other):
        '''call to perform other.update(self)'''
        return self.call_item_method(other, 'update')

    def __le__(self, other):
        '''call to perform other.update(self), return self'''
        self.call_item_method(other, 'update')
        return self

    def __gt__(self, other):
        '''call to perform other.reload(self)'''
        return self.call_item_method(other, 'reload')

    def __ge__(self, other):
        '''call to perform other.reload(self), return self'''
        self.call_item_method(other, 'reload')
        return self


class Request(object):
    '''a callable request compatible with Pulp.send''' 
    def __init__(self, method, path, data=None, headers=None):
        self.method = method
        self.path = path
        self.data = data
        self.headers = headers

    def __call__(self, url, auth):
        return requests.Request(
            self.method,
            normalize_url(url + "/" + pulp_path + "/" + self.path),
            auth=auth,
            data=self.data,
            headers=self.headers
        ).prepare()


    def __repr__(self):
        return self.__class__.__name__ + "(%r, %r, data=%r, headers=%r)" % (self.method, self.path, self.data, self.headers)

def format_response(response):
    '''format some response attributes'''
    return '>response:\n>c %s\n>u %s\n>t %s\n' % (response.status_code, response.url, response.text)
