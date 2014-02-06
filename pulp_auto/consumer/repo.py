from cli_class import Command, ConsumerCommand
from pulp_auto.hasdata import HasData
from pulp_auto.repo import Repo as APIRepo
import re, ConfigParser, StringIO

class BaseRepo(HasData):
    """Consumer repos"""
    relevant_data_keys = APIRepo.relevant_data_keys
    required_data_keys = APIRepo.required_data_keys
    header_delimiter = '+' + '-' * 70 + '+\n'  
    header_fields_count = 2

    @classmethod
    def strip_header(cls, txt):
        return txt.split(cls.header_delimiter)[cls.header_fields_count].strip()

    @classmethod
    def parse(cls, txt):
        """read txt (output of pulp-consumer <type> repos command) and convert it to base types"""
        # parsing with intermediate ConfigParser
        # make all id: <repo_id> fields to section names [<repo_id>]
        fp = StringIO.StringIO(re.sub(r'[Ii]d\s*:\s*(.*)', r'[\1]', txt))
        cfgp = ConfigParser.ConfigParser()
        cfgp.readfp(fp)
        return [dict(cfgp.items(section) + [('id', section)]) for section in cfgp.sections()]

    @classmethod
    def list(cls, remote):
        raise NotImplementedError()
        
    @classmethod
    def get(cls, remote, id):
        try:
            return filter(lambda x: x.id == id, cls.list(remote))[0]
        except IndexError:
            # no such item
            raise ValueError("could not find %s().id == %s" % (cls.__name__, id))

    @property
    def id(self):
        return self.data['id']

    @id.setter
    def id(self, value):
        self.data['id'] = value
        

class RpmRepo(BaseRepo):
    """Rpm Consumer repos"""
    @classmethod
    def list(cls, remote):
        items = cls.parse(cls.strip_header(remote(ConsumerCommand('rpm', 'repos'))))
        return map(lambda item: cls(item), items)


class PuppetRepo(BaseRepo):
    """Pulp consumer repos"""
    @classmethod
    def list(cls, remote):
        items = cls.parse(cls.strip_header(remote(ConsumerCommand('puppet', 'repos'))))
        return map(lambda item: cls(item), items)


class YumRepo(BaseRepo):
    """Yum consumer repos"""
    # yum repos are different than the rest, just the id field seems to make sense
    relevant_data_keys = ['id']
    @classmethod
    def strip_header(cls, txt):
        return txt

    @classmethod
    def parse(cls, txt):
        pass

    @classmethod
    def list(cls, con):
        from connection import Connection
        # assert proper connection instance
        con = Connection.from_connection(con)
        # yum has a module that can be used
        ybs = con.connection.rpyc.modules.yum.YumBase()
        remote_repos = [{'id': repo.id} for repo in ybs.repos.listEnabled()]
        return map(lambda item: cls(item), remote_repos)
