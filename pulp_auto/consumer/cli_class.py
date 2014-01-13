from patchwork import (Connection, Expect)
from ConfigParser import ConfigParser
import contextlib

class Command(object):
    '''represents an authorized pulp-consumer command to be executed in the plumbum fashion'''
    consumer_path = '/bin/pulp-consumer' 

    def __init__(self, *args, **kvs):
        '''create the command representation convert attr_name=attr_value to --attr-name=attr_value
        cli string args tuple
        '''
        # merge args and kvs together to form a huge tuple
        # that plumbum understands
        self.args = reduce(
            lambda the_tuple, key_value_pair: the_tuple + key_value_pair,
            [ \
                (Command.key_to_argname(key), Command.value_to_argvalue(value)) \
                for key, value in kvs.items() if value is not None \
            ],
            tuple(args)
        )

    @staticmethod
    def key_to_argname(key):
        return '--' + str(key).replace('_', '-')

    @staticmethod
    def value_to_argvalue(value):
        return str(value)

    @staticmethod
    def kvs_to_args(**kvs):
        return 

    def __call__(self, remote, auth=['admin', 'admin']):
        '''create plumbum-fashion command over remote with provided authentication'''
        return remote[self.consumer_path][('-u', str(auth[0]), '-p', str(auth[1])) + self.args]

    def __str__(self):
        return str(self.args)

class Cli(object):
    '''a consumer cli handle'''
    def __init__(self, hostname='localhost', ssh_key=None):
        self.connection = Connection(instance=hostname, key_filename=ssh_key)
        self._registered = False

    def configure(self, pulp_hostname='localhost', pulp_port=443):
        '''set consumer cli hostname and port'''
        self.pulp_hostname = pulp_hostname
        self.pulp_port = pulp_port
        config_filename = '/etc/pulp/consumer/consumer.conf'
        config = ConfigParser()
        with self.connection.rpyc.builtin.open(config_filename) as fp:
            config.readfp(fp)
        config.set('server', 'host', pulp_hostname)
        config.set('server', 'port', pulp_port)
        with self.connection.rpyc.builtin.open(config_filename, 'w+') as fp:
            config.write(fp)

    def remote(self, command):
        '''return a Plubmub bound remote command instance of pulp-consumer and args'''
        if not self._registered:
            raise RuntimeError("Can't issue remote calls over an un-registered consumer cli")
        return command(remote=self.connection.pbm, auth=self.pulp_auth)

    def __call__(self, command):
        '''return remote pulp-consumer command result'''
        return self.remote(command)()

    def register(self, consumer_id, pulp_auth=['admin', 'admin'], description=None, display_name=None, note=None):
        '''register the consumer to pulp with specified id'''
        self.consumer_id = consumer_id
        self.pulp_auth = pulp_auth
        self._registered = True
        command = Command('register', consumer_id=consumer_id, description=description,
                            display_name=display_name, note=note)
        return self(command)

    def unregister(self, command=Command('unregister')):
        result = self(command)
        self._registered = False
        return result

    @classmethod
    def ready_instance(cls, consumer_id, hostname='localhost', ssh_key=None, pulp_hostname='localhost',
                        pulp_port=443, pulp_auth=['admin', 'admin'], description=None, display_name=None, note=None):
        '''instantiate a ready-to-use cli i.e. configured and registered'''
        cli = cls(hostname, ssh_key)
        cli.configure(pulp_hostname, pulp_port)
        cli.register(consumer_id, pulp_auth, description, display_name, note)
        return cli

