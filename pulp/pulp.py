import requests


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
