"""
pulp node Item
"""
from pulp_auto.consumer.consumer_class import Consumer
from pulp_auto.repo import NODE_DISTRIBUTOR_TYPE_ID, NodeDistributor


class Node(Consumer):
    '''Node is a Consumer...'''

    @classmethod
    def register(cls, pulp, id, display_name=None, description=None, rsa_pub=None,
            update_strategy='additive'):
        return super(Node, cls).register(pulp, id, description=description, display_name=display_name,
                notes={'_child-node': True, '_node-update-strategy': update_strategy},
                rsa_pub=rsa_pub)

    def activate(self, pulp, update_strategy='additive'):
        '''activate/promote this consumer to a node'''
        return self.update(
            pulp,
            data={
                'delta': {
                    'notes': {
                        '_child-node': True,
                        '_node-update-strategy': update_strategy
                    }
                }
            }
        )

    def deactivate(self, pulp):
        '''deactivate the node interface'''
        return self.update(
            pulp,
            data={
                'delta': {
                    'notes': {
                        '_child-node': None,
                        '_node-update_strategy': None
                    }
                }
            }
        )

    def bind_repo(self, pulp, repo_id, distributor_id=NodeDistributor.default_id,
                config={'strategy': 'additive'}):
        '''bind this node to a repo'''
        return self.bind_distributor(pulp, repo_id, distributor_id, config=config,
                notify_agent=False)

    def unbind_repo(self, pulp, repo_id, distributor_id=NodeDistributor.default_id):
        '''unbind this node from a repo'''
        return self.unbind_distributor(pulp, repo_id, distributor_id)

    def sync_repo(self, pulp, repo_id):
        '''sync a bound repo to this node'''
        return self.update_unit(pulp, type_id='repository', unit_key=dict(repo_id=repo_id),
                    options={})
