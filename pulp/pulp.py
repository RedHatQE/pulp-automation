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
        self._async = False

    def send(self, request):
        '''send a request; the request has to be callable that accepts url and auth params'''
        if self._async:
            # when in async mode, just "queue" requests
            self.last_request += (request(self.url, self.auth), )
            return
        self.last_request = request(self.url, self.auth)
        self.last_response = self.session.send(self.last_request, verify=self.verify)
        if self._asserting:
            assert self.is_ok, 'pulp was not OK:\n' + \
                format_preprequest(self.last_request) + format_response(self.last_response)
            pass
        return self.last_response

    @property
    def is_ok(self):
        if self.last_response is None:
            return True
        check = lambda x: x.status_code >= 200 and x.status_code < 400
        if isinstance(self.last_response, tuple):
            return reduce(lambda x, y : x and check(y), self.last_response, True)
        return check(self.last_response)

    @contextlib.contextmanager
    def asserting(self, value=True):
        '''turn on/off asserting responses in self.send()'''
        old_value = self._asserting
        self._asserting = value
        try:
            yield
        finally:
            self._asserting = old_value

    @contextlib.contextmanager
    def async(self, timeout=None):
        '''enter a async/concurent--send context; pending requests will be processed at context exit'''
        self.last_request = ()
        self._async = True
        try:
            yield # gather send requests here
            # process pending requests
            import gevent
            from gevent import monkey
            monkey.patch_all(thread=False, select=False)
            jobs = [gevent.spawn(self.session.send, request) for request in self.last_request]
            gevent.joinall(jobs, timeout=timeout)
            self.last_response = tuple([job.value for job in jobs])
            if self._asserting:
                assert self.is_ok, 'pulp was not OK:\n' + \
                    format_preprequest(preprequest) + format_response(self.last_response)
        finally:
            self._async = False


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


class ResponseLike(object):
    '''provide comparison between requests.Result and a code/text/data container'''
    def __init__(self, status_code=200, text=None):
        self.status_code = status_code
        self.text = text

    def __eq__(self, other):
        if self.text is not None:
            return self.status_code, self.text == other.status_code, other.text
        return self.status_code == other.status_code

    def __repr__(self):
        return  type(self).__name__ + '(status_code=%(status_code)s, text=%(text)s)' % self.__dict__

def format_response(response):
    '''format some response attributes'''
    import pprint
    try:
        text = pprint.pformat(response.json())
    except Exception:
        text = response.text
    return '>response:\n>c %s\n>u %s\n>t\n%s\n' % (response.status_code, response.url, text)

def format_preprequest(preprequest):
    '''format some prepared request attributes'''
    return '>preprequest:\n>m %(method)s\n>p %(url)s\n>b %(body)s\n>h %(headers)s\n' % preprequest.__dict__
