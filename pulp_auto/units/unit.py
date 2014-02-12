from pulp_auto.item import Item
from pulp_auto import (normalize_url, path_join, path_split, strip_url)
from pulp_auto.pulp import Request
from pulp_auto.namespace import (Namespace, load_ns)

class UnitFactory(Item):
    """to dispatch Units instantiation"""

    # type of unit to instantiate is dependant on the
    # response's data['_content_type_id'] value
    # and its path e.g. /content/units/rpm/
    type_map = {}

    path = '/'

    @classmethod
    def register(cls, type_name, unit_type):
        # register a (typename, type) pair
        cls.type_map.update({type_name: unit_type})


    @classmethod
    def from_data(cls, data):
        '''instantiate proper unit type instances based on data'''
        if not isinstance(data, list):
            type_id = data['_content_type_id']
            # make sure there's type to instantiate to
            assert type_id in cls.type_map, "%s not found in type_map"\
                    % type_id
            return type_map[type_id](data)
        ret = []
        for item in data:
            type_id = data['_content_type_id']
            assert type_id in cls.type_map, "%s not found in type_map"\
                    % type_id
            ret.append(type_map[type_id](data))
        return ret

    @classmethod
    def from_response(cls, response):
        '''instantiate proper unit item from a response'''
        data = response.json()
        return cls.from_data(data)

class MetaUnit(type):
    '''a MetaClass to perform Unit type registration at Unit Factory'''
    def __new__(mcs, name, bases, dict):
        '''register unit type instance '''
        unit_type_instance = type.__new__(mcs, name, bases, dict)
        UnitFactory.register(unit_type_instance.path_type(), unit_type_instance)
        return unit_type_instance

class AbstractUnit(Item):
    """Units are Items just like the rest. This is rather an abstract
    Unit type"""
    # all units are identified by these keys, thus they're required
    # to be present in data during initialization
    required_data_keys = ['_content_type_id', '_id']
    path = '/content/units/'


    # all sub classes shall be registered at the UnitFactory
    __metaclass__ = MetaUnit

    # Units have a distinctive type_id
    @property
    def type_id (self):
            return self.data['_content_type_id']

    @type_id.setter
    def type_id(self, value):
            self.data['_content_type_id'] = value

    # and the .id field is named _id
    @property
    def id(self):
            return self.data['_id']

    @id.setter
    def id(self, value):
            self.data['_id'] = value

    @classmethod
    def from_response(cls, response):
            '''wrapper for Unit factory'''
            return UnitFactory.from_response(response)

    @classmethod
    def path_type(cls):
        '''what type the cls.path refers to'''
        return path_split(cls.path)[-2]

    def __init__(self, data={}):
        super(AbstractUnit, self).__init__(data)
        path_type = type(self).path_type()
        assert self.type_id == path_type, "self.path different from self.type_id: %s, %s" % (self.type_id, path_type)

class RpmUnit(AbstractUnit):
    '''rpm-specific unit code'''
    path = AbstractUnit.path + "/rpm/"
    relevant_data_keys = AbstractUnit.relevant_data_keys + ['name', 'version', 'release', 'arch']


class DistributionUnit(AbstractUnit):
    '''distribution-specific unit code'''
    path = AbstractUnit.path + "/distribution/"
    # TODO: relevant_data_keys



class DrpmUnit(AbstractUnit):
    '''drpm-specific unit code'''
    path = AbstractUnit.path + "/drpm/"
    # TODO: relevant_data_keys


class ErratumUnit(AbstractUnit):
    '''erratum-specific unit code'''
    path = AbstractUnit.path + "/erratum/"
    # TODO: relevant_data_keys


class IsoUnit(AbstractUnit):
    '''iso-specific unit code'''
    path = AbstractUnit.path + "/iso/"
    # TODO: relevant_data_keys


class PackageCategoryUnit(AbstractUnit):
    '''package-category-specific unit code'''
    path = AbstractUnit.path + "/package_category/"
    # TODO: relevant_data_keys


class PackageGroupUnit(AbstractUnit):
    '''package-group-specific unit code'''
    path = AbstractUnit.path + "/package_group/"
    # TODO: relevant_data_keys


class PuppetModuleUnit(AbstractUnit):
    '''puppet-module-specific unit code'''
    path = AbstractUnit.path + "/puppet_module/"
    # TODO: relevant_data_keys


class SrpmUnit(AbstractUnit):
    '''Srpm-specific unit code'''
    path = AbstractUnit.path + "/srpm/"
    # TODO: relevant_data_keys


class YumRepoMetadataFileUnit(AbstractUnit):
    '''Yum-metada unit code'''
    path = AbstractUnit.path + "/yum_repo_metadata_file/"
    # TODO: relevant_data_keys

class PackageEnvironmentUnit(AbstractUnit):
    '''package environments (collections of package groups)'''
    path = AbstractUnit.path + "/package_environment/"
    # TODO: relevant_data_keys

