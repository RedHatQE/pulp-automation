import requests, json, contextlib
from . import (normalize_url, path_join, path as pulp_path)


class Pulp(object):
    '''Pulp handle'''
    def __init__(self, url, auth=None, verify=False, asserting=False):
        self.session = requests.Session()
        self.url = url
        self.auth = auth
        self.verify = verify
        self.last_response = None
        self.last_request = None
        self._asserting = asserting

    def send(self, request):
        '''send a request; the request has to be callable that accepts url and auth params'''
        self.last_request = request(self.url, self.auth)
        self.last_response = self.session.send(self.last_request, verify=self.verify)
        if self._asserting:
            assert self.is_ok, 'pulp was not OK:\n' + \
                format_preprequest(preprequest) + format_response(self.last_response)
        return self.last_response

    @property
    def is_ok(self):
        if self.last_response is None:
            return True
        return self.last_response.status_code >= 200 and self.last_response.status_code < 400

    @contextlib.contextmanager
    def asserting(self, value=True):
        '''turn on/off asserting responses in self.send()'''
        old_value = self._asserting
        self._asserting = value
        try:
            yield
        finally:
            self._asserting = old_value


class Request(object):
    '''a callable request compatible with Pulp.send''' 
    def __init__(self, method, path, data={}, headers={'Content-Type': 'application/json'}):
        self.method = method
        self.path = path
        self.data = json.dumps(data)
        self.headers = headers

    def __call__(self, url, auth):
        return requests.Request(
            self.method,
            normalize_url(path_join(url, pulp_path, self.path)),
            auth=auth,
            data=self.data,
            headers=self.headers
        ).prepare()

    def __repr__(self):
        return self.__class__.__name__ + "(%r, %r, data=%r, headers=%r)" % (self.method, self.path, self.data, self.headers)

def format_response(response):
    '''format some response attributes'''
    return '>response:\n>c %s\n>u %s\n>t %s\n' % (response.status_code, response.url, response.text)

def format_preprequest(preprequest):
    '''format some prepared request attributes'''
    return '>preprequest:\n>m %(method)s\n>p %(url)s\n>b %(body)s\n>h %(headers)s\n' % preprequest.__dict__
