from pulp_auto.hasdata import HasData
from cli_class import Command
from connection import Connection
import re, ConfigParser, StringIO

class RpmUnit(HasData):
    required_data_keys = ['name']
    relevant_data_keys = ['name', 'version', 'release', 'arch']
    
    @classmethod
    def parse(cls, txt):
        """read txt (output of rpm -qia command) and convert it to base types"""
        fp = StringIO.StringIO(txt)
        cfpg = ConfigParser.ConfigParser()
        cfpg.readfp(fp)
        return [dict(cfpg.items(section) + [('name', section)]) for section in cfpg.sections()]

    @classmethod
    def list(cls, con):
        con = Connection.from_connection(con)
        items = cls.parse(con(Command('rpm', '-qa', '--queryformat', r'\[%{NAME}\]\nVersion:%{VERSION}\nRelease:%{RELEASE}\nArch:%{ARCH}\nInstall_time:%{INSTALLTIME:date}\nGroup:%{GROUP}\nSize:%{SIZE}\nLicense:%{LICENSE}\nSummary:%{SUMMARY}\nPackager:%{PACKAGER}\nVendor:%{VENDOR}\n')))
        return map(lambda item: cls(item), items)

    @classmethod
    def get(cls, con, id):
        try:
            return filter(lambda x: x.id == id, cls.list(con))[0]
        except IndexError:
            # no such item
            raise ValueError("could not find %s().id == %s" % (cls.__name__, id))

    @property
    def id(self):
        return self.data['id']

    @id.setter
    def id(self, value):
        self.data['id'] = value
 
