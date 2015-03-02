"""
pulp node Item
"""
from pulp_auto.consumer.consumer_class import Consumer

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
        return self.update(pulp, data={'delta': {'_child-node': True, '_node-update-strategy': update_strategy}})

    def deactivate(self, pulp):
        '''deactivate the node interface'''
        return self.update(pulp, data={'delta': {'_child-node': None, '_node-update_strategy': None}})
