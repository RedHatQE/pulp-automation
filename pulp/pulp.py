import requests
from . import (normalize_url, path as pulp_path)


class Pulp(object):
    '''Pulp handle'''
    def __init__(self, url, auth=None, verify=False):
        self.session = requests.Session()
        self.url = url
        self.auth = auth
        self.verify = verify
        self.last_result = None

    def send(self, request):
        '''send a request; the request has to be callable that accepts url and auth params'''
        self.last_result = self.session.send(request(self.url, self.auth), verify=self.verify)
        return self.last_result

    @property
    def is_ok(self):
        if self.last_result is None:
            return True
        return self.last_result.status_code >= 200 and self.last_result.status_code < 400


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


