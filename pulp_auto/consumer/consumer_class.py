import json, requests, contextlib
from .. import (namespace, normalize_url, path_join, path_split, strip_url, item, Request, handler)
import logging
from .. import common_consumer
from pulp_auto.item import ScheduledAction
from pulp_auto.common_consumer import Binding
log = logging.getLogger(__name__)


class Event(item.AssociatedItem):
    path='/history/'
    relevant_data_keys = ['event_type', 'limit', 'sort', 'start_date', 'end_date']

class ConsumersApplicability(object):
    path = '/consumers/'

    @staticmethod
    def request(method, path, data={}, params={}):
        return Request(method, path_join(ConsumersApplicability.path, path), params=params, data=data)

    @staticmethod
    def regenerate(
        pulp,
        data={},
        path='/actions/content/regenerate_applicability/'
    ):
        return pulp.send(ConsumersApplicability.request('POST', path=path, data=data))

    @staticmethod
    def query(
        pulp,
        data={},
        path='/content/applicability/'
    ):
        return pulp.send(ConsumersApplicability.request('POST', path=path, data=data))

class Consumer(common_consumer.ProtoConsumer):
    '''consumer item implementation'''
    path = '/consumers/'
    relevant_data_keys = ['id', 'display_name']

    @classmethod
    @handler.logged(log.debug)
    def register(cls, pulp, id, display_name=None, description=None, notes=None, rsa_pub=None):
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
                    'notes': notes,
                    'rsa_pub': rsa_pub
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

    def list_bindings(self, pulp):
        return Binding.from_response(pulp.send(self.request('GET', path=Binding.path)))

    def get_repo_bindings(self, pulp, repo_id):
        return Binding.from_response(pulp.send(self.request('GET', path=path_join(Binding.path, repo_id))))

    def get_single_binding(self, pulp, repo_id, distributor_id):
        return Binding.from_response(pulp.send(self.request('GET', path=path_join(Binding.path, repo_id, distributor_id))))

    def get_history(self, pulp, params={}):
        return Event.from_response(pulp.send(self.request('GET', path=Event.path, params=params)))

    def schedule_install(
        self,
        pulp,
        schedule,
        type_id,
        unit_key,
        options=None
    ):
        data = {
            "units": [{"unit_key": unit_key, "type_id": type_id}],
            "options": options
        }
        return self.create_scheduled_action(pulp, action='/content/install/', schedule=schedule, data=data)

    def schedule_update(
        self,
        pulp,
        schedule,
        type_id,
        unit_key,
        options=None
    ):
        data = {
            "units": [{"unit_key": unit_key, "type_id": type_id}],
            "options": options
        }
        return self.create_scheduled_action(pulp, action='/content/update/', schedule=schedule, data=data)

    def applicability(
        self,
        pulp,
        path='/actions/content/regenerate_applicability/'
    ):
        return pulp.send(self.request('POST', path=path))

    def schedule_uninstall(
        self,
        pulp,
        schedule,
        type_id,
        unit_key,
        options=None
    ):
        data = {
            "units": [{"unit_key": unit_key, "type_id": type_id}],
            "options": options
        }
        return self.create_scheduled_action(pulp, action='/content/uninstall/', schedule=schedule, data=data)

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
