from stitches import (Connection, Expect)
from ConfigParser import ConfigParser
from command import Command
from connection import Connection
import contextlib, re
import plumbum


class ConsumerCommand(Command):
    '''represents an authorized pulp-consumer command to be executed in the plumbum fashion'''
    consumer_command = '/usr/bin/pulp-consumer'

    def __init__(self, *args, **kvs):
        super(ConsumerCommand, self).__init__(self.consumer_command, *args, **kvs)

    def __call__(self, remote, auth=['admin', 'admin']):
        '''create plumbum-fashion command over remote with provided authentication'''
        self.args = ('-u', str(auth[0]), '-p', str(auth[1])) + self.args
        return super(ConsumerCommand,self).__call__(remote)


class Cli(Connection):
    '''a consumer cli handle'''
    def __init__(self, hostname='localhost', ssh_key=None):
        super(Cli, self).__init__(hostname, ssh_key)
        self.pulp_auth = None
        self.pulp_hostname = None
        self.pulp_port = None

    def remote(self, command):
        '''return a Plubmub bound remote command instance of pulp-consumer and args'''
        return command(remote=self.connection.pbm, auth=self.pulp_auth)

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
        try:
            # use systemctl or service
            self.connection.pbm['systemctl']['--version']
        except plumbum.CommandNotFound as e:
            # rhel?
            command = Command('/sbin/service', 'goferd', 'restart')(self.connection.pbm)
        else:
            # fedora?
            command  = Command('/bin/systemctl', 'restart', 'goferd.service')(self.connection.pbm)
        command()

    def register(self, consumer_id, pulp_auth=['admin', 'admin'], description=None, display_name=None, note=None):
        '''register the consumer to pulp with specified id'''
        self.consumer_id = consumer_id
        self.pulp_auth = pulp_auth
        command = ConsumerCommand('register', consumer_id=consumer_id, description=description,
                            display_name=display_name, note=note)
        return self(command)

    def unregister(self, command=ConsumerCommand('unregister')):
        result = self(command)
        self._registered = False
        return result

    @classmethod
    def ready_instance(
            cls,
            id,
            hostname='localhost',
            ssh_key=None,
            pulp={
                'hostname': 'localhost',
                'port': 443,
                'auth': ['admin', 'admin']
            },
            description=None,
            display_name=None,
            note=None,
            **kvs
    ):
        '''instantiate a ready-to-use cli i.e. configured and registered'''
        cli = cls(hostname, ssh_key)
        cli.configure(pulp.get('hostname', 'localhost'), pulp.get('port', 443))
        cli.register(id, pulp.get('auth', ['admin', 'admin']), description, display_name, note)
        return cli

