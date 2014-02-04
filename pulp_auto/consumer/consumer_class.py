import json, requests, contextlib
from .. import (namespace, normalize_url, path_join, path_split, strip_url, item, Request)


class Binding(item.AssociatedItem):
    path='/bindings/'
    relevant_data_keys = ['repo_id', 'consumer_id', 'distributor_id']

class Consumer(item.Item):
    '''consumer item implementation'''
    path = '/consumers/'
    relevant_data_keys = ['id', 'display_name']

    @classmethod
    def register(cls, pulp, id, display_name=None, description=None, notes=None):
        '''register new consumer
        return a Consumer instance made out of pulp response
        '''
        # the response contains private&public key in certificate field
        # consequent reloads give just public key
        # it is vital to return an cls.from_response instance
        with pulp.asserting(True):
            response = cls(
                {
                    'id': id,
                    'display_name': display_name,
                    'description': description,
                    'notes': notes
                }
            ).create(pulp)
        return cls.from_response(response)

    def bind_distributor(self, pulp, data):
        '''bind this consumer to a repo distributor'''
        return pulp.send(self.request('POST', path=Binding.path, data=data))

    def unbind_distributor(self, pulp, repo_id, distributor_id):
        '''unbind this consumer from a given repo distributor'''
        return pulp.send(self.request('DELETE', path=path_join(Binding.path, repo_id, distributor_id)))

    def list_bindings(self, pulp):
        return Binding.from_response(pulp.send(self.request('GET', path=Binding.path)))

    def get_repo_bindings(self, pulp, repo_id):
        return Binding.from_response(pulp.send(self.request('GET', path=path_join(Binding.path, repo_id))))

    @property
    def certificate(self):
        return self.data['certificate']

    @certificate.setter
    def certificate(self, cert):
        self.data['certificate'] = cert

    @contextlib.contextmanager
    def tmp_certfile(self, closed=False):
        '''context manager creating a named temporary cert file'''
        import tempfile
        certfile = tempfile.NamedTemporaryFile(delete=False)
        certfile.write(self.certificate)
        certfile.seek(0)
        if closed:
            certfile.close()
        try:
            yield certfile
        finally:
            if not certfile.closed:
                certfile.close()
            certfile.unlink(certfile.name)

SAMPLE_DISTRIBUTOR_BIND_DATA = {
    "repo_id": "test-repo",
    "distributor_id": "dist-1",
    "options": None,  # Options of consumer handler
    "notify_agent": True,  # by default
    "bindning_config": None
}
