import json, namespace, requests
from . import (normalize_url, path_join, path_split, strip_url)
from pulp_auto import (Request, )
from item import (Item, AssociatedItem)


class Binding(AssociatedItem):
    path='/bindings/'
    relevant_data_keys = ['repo_id', 'consumer_id', 'distributor_id']

class Consumer(Item):
    '''consumer item implementation'''
    path = '/consumers/'
    relevant_data_keys = ['id', 'display_name']

    def create(self, pulp):
        '''creating consumer gives vital data: private key in cert; one can't fetch it otherwise
        The private key is preserved by an implicit self.data update. A reload destroys it, though.
        '''
        response = super(Consumer, self).create(pulp)
        tmp_consumer = type(self).from_response(response)
        self.data = tmp_consumer.data
        return response
        

    def bind_distributor(self, pulp, data):
        '''bind this consumer to a repo distributor'''
        return pulp.send(self.request('POST', path=Binding.path, data=data))

    def unbind_distributor(self, pulp, repo_id, distributor_id):
        '''unbind this consumer from a given repo distributor'''
        return pulp.send(self.request('DELETE', path=path_join(Binding.path, repo_id ,distributor_id)))

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

SAMPLE_DISTRIBUTOR_BIND_DATA = {
    "repo_id": "test-repo",
    "distributor_id": "dist-1",
    "options": None, # Options of consumer handler
    "notify_agent": True, # by default
    "bindning_config": None
}
