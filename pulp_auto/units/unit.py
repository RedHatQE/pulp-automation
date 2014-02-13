from pulp_auto.item import Item
from pulp_auto import (normalize_url, path_join, path_split, strip_url)
from pulp_auto.pulp import Request
from pulp_auto.namespace import (Namespace, load_ns)
from pulp_auto import path_fields

class UnitFactory(object):
    """to dispatch Units instantiation"""

    # type of unit to instantiate is dependant on the
    # response's data['_content_type_id'] value
    # and its path e.g. /content/units/rpm/
    type_map = Namespace()

    path = '/'

    @classmethod
    def register(cls, unit_type):
        # register a unit_super_type.unit_type item e.g. type_map.units.rpm
        fields = path_fields(unit_type.path)
        if len(fields) <= 2:
            # probably, AbstractUnit is being registered
            return
        unit_super_type_name, unit_type_name = path_fields(unit_type.path)[1:3]
        if unit_super_type_name not in cls.type_map:
            cls.type_map[unit_super_type_name] = Namespace()
        cls.type_map[unit_super_type_name].update({unit_type_name: unit_type})

    @classmethod
    def process_item_data(cls, data):
        '''figure out the type based on the href e.g. units/rpm -> RpmUnit, orphans/rpm -> RpmOrphan'''
        path = '.'.join(path_fields(data['_href'])[-3:-1])
        # make sure there's type to instantiate to
        # this utilizes the namespace['a.b.c....'] item locations
        assert path in cls.type_map, "path %s not found in type_map" % path
        # make sure the _href matches the type_id
        assert data['_content_type_id'] == path_fields(data['_href'])[-2], \
                "_content_type_id doesn't match href: %s" % data
        return cls.type_map[path](data)

    @classmethod
    def from_data(cls, data):
        '''instantiate proper unit type instances based on data'''
        if not isinstance(data, list):
            return cls.process_item_data(data)
        return map(lambda x: cls.process_item_data(x), data)

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
        UnitFactory.register(unit_type_instance)
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
        return path_fields(cls.path)[-1]

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
