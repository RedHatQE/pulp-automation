import json, requests, contextlib
from . import (namespace, normalize_url, path_join, path_split, strip_url, item, Request, handler)
from pulp_auto import item
import logging
log = logging.getLogger(__name__)


class Binding(item.AssociatedItem):
    path='/bindings/'
    relevant_data_keys = ['repo_id', 'consumer_id', 'distributor_id']


class ProtoConsumer(item.Item):

    def bind_distributor(self, pulp, repo_id, distributor_id, notify_agent=True, config=None):
        '''bind this consumer/consumer group to a repo distributor'''
        data = {
            'repo_id': repo_id,
            'distributor_id': distributor_id,
            'notify_agent': notify_agent,
            'config': config
        }
        return pulp.send(self.request('POST', path=Binding.path, data=data))

    def unbind_distributor(self, pulp, repo_id, distributor_id):
        '''unbind this consumer/consumer group  from a given repo distributor'''
        return pulp.send(self.request('DELETE', path=path_join(Binding.path, repo_id, distributor_id)))

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

    def update_unit(
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
        '''update single unit'''
        data = {
            "units": [{"unit_key": unit_key, "type_id": type_id}],
            "options" : options
        }
        return pulp.send(
            self.request(
                'POST',
                path='/actions/content/update/',
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

