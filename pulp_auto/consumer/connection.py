from stitches import Connection as StitchesConnection

class Connection(object):
    def __init__(self, hostname='localhost', ssh_key=None):
        self.hostname = hostname
        self.ssh_key = ssh_key
        self.connection = StitchesConnection(instance=hostname, key_filename=ssh_key)

    def remote(self, command):
        '''return a Plubmub bound remote command instance of a command'''
        return command(remote=self.connection.pbm)

    def __call__(self, command):
        '''return remote pulp-consumer command result'''
        return self.remote(command)()

    @classmethod
    def from_connection(cls, connection):
        return cls(hostname=connection.hostname, ssh_key=connection.ssh_key)


