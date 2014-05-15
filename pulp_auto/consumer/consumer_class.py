import json, requests, contextlib
from .. import (namespace, normalize_url, path_join, path_split, strip_url, item, Request, handler)
import logging
log = logging.getLogger(__name__)

class Binding(item.AssociatedItem):
    path='/bindings/'
    relevant_data_keys = ['repo_id', 'consumer_id', 'distributor_id']

class Event(item.AssociatedItem):
    path='/history/'
    relevant_data_keys = ['event_type', 'limit', 'sort', 'start_date', 'end_date']

class Consumer(item.Item):
    '''consumer item implementation'''
    path = '/consumers/'
    relevant_data_keys = ['id', 'display_name']

    @classmethod
    @handler.logged(log.debug)
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

    @classmethod
    @handler.logged(log.debug)
    def from_response(cls, response):
        '''first ever (creating) response requires custom handling'''
        data = response.json()
        if 'consumer' in data:
            # first ever response; custom handling
            log.info('new consumer registered: %s' % data['consumer']['display_name'])
            consumer_data = data['consumer']
            assert 'certificate' in data, "certificate key missing in first ever consumer response"
            consumer_data['certificate'] = data['certificate']
            return cls(data=consumer_data)
        return super(Consumer, cls).from_response(response)

    def bind_distributor(self, pulp, repo_id, distributor_id, config=None):
        '''bind this consumer to a repo distributor'''
        data = {
            'repo_id': repo_id,
            'distributor_id': distributor_id,
            'config': config
        }
        return pulp.send(self.request('POST', path=Binding.path, data=data))

    def unbind_distributor(self, pulp, repo_id, distributor_id):
        '''unbind this consumer from a given repo distributor'''
        return pulp.send(self.request('DELETE', path=path_join(Binding.path, repo_id, distributor_id)))

    def list_bindings(self, pulp):
        return Binding.from_response(pulp.send(self.request('GET', path=Binding.path)))

    def get_repo_bindings(self, pulp, repo_id):
        return Binding.from_response(pulp.send(self.request('GET', path=path_join(Binding.path, repo_id))))

    def get_single_binding(self, pulp, repo_id, distributor_id):
        return Binding.from_response(pulp.send(self.request('GET', path=path_join(Binding.path, repo_id, distributor_id))))

    def get_history(self, pulp, params={}):
        return Event.from_response(pulp.send(self.request('GET', path=Event.path, params=params)))

    def install_unit(
        self,
        pulp,
        unit_key,
        type_id,
        options = {
            "apply": True,
            "reboot": False,
            "importkeys": False
        }
    ):
        '''install single unit'''
        data = {
            "units": [{"unit_key": unit_key, "type_id": type_id}],
            "options" : options
        }
        return pulp.send(
            self.request(
                'POST',
                path='/actions/content/install/',
                data=data
            )
        )

    def uninstall_unit(
        self,
        pulp,
        unit_key,
        type_id,
        options = {
            "apply": True,
            "reboot": False
        }
    ):
        '''remove single unit'''
        data = {
            "units": [{"unit_key": unit_key, "type_id": type_id}],
            "options": options
        }
        return pulp.send(
            self.request(
                'POST',
                path='/actions/content/uninstall',
                data=data
            )
        )

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
