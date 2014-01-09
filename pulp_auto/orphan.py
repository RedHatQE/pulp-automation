from item import Item
from . import (normalize_url, path_join, path_split, strip_url)
from pulp_auto import Request
from namespace import (Namespace, load_ns)

class AbstractOrphan(Item):
    """Orphans are Items just like the rest. This is rather an abstract
    Orphan type"""
    # all orphans are identified by these keys, thus they're required
    # to be present in data during initialization
    required_data_keys = ['_content_type_id', '_id']
    path = '/content/orphans/'

    # Orphans have a distinctive type_id 
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
            '''wrapper for orphan factory'''
            return OrphanFactory.from_response(response)
    
    @classmethod
    def delete_all(cls, pulp):
            '''delete all orphans of particular type in pulp instance'''
            return pulp.send(Request('DELETE', cls.path))

    def __init__(self, data={}):
        super(AbstractOrphan, self).__init__(data)
        path_type = path_split(self.path)[-2]
        assert self.type_id == path_type, "self.path different from self.type_id: %s, %s" % (self.type_id, path_type)

class RpmOrphan(AbstractOrphan):
    '''rpm-specific orphan code'''
    path = AbstractOrphan.path + "/rpm/"
    
    # expand as needed
    relevant_data_keys = AbstractOrphan.relevant_data_keys + ['arch', 'version']


class DistributionOrphan(AbstractOrphan):
    '''distribution-specific orphan code'''
    path = AbstractOrphan.path + "/distribution/"


class DrpmOrphan(AbstractOrphan):
        '''drpm-specific orphan code'''
        path = AbstractOrphan.path + "/drpm/"


class ErratumOrphan(AbstractOrphan):
    '''erratum-specific orphan code'''
    path = AbstractOrphan.path + "/erratum/"


class IsoOrphan(AbstractOrphan):
        '''iso-specific orphan code'''
        path = AbstractOrphan.path + "/iso/"


class PackageCategoryOrphan(AbstractOrphan):
        '''package-category-specific orphan code'''
        path = AbstractOrphan.path + "/package_category/"


class PackageGroupOrphan(AbstractOrphan):
        '''package-group-specific orphan code'''
        path = AbstractOrphan.path + "/package_group/"


class PuppetModuleOrphan(AbstractOrphan):
        '''puppet-module-specific orphan code'''
        path = AbstractOrphan.path + "/puppet_module/"


class SrpmOrphan(AbstractOrphan):
        '''Srpm-specific orphan code'''
        path = AbstractOrphan.path + "/srpm/"


class YumRepoMetadataFileOrphan(AbstractOrphan):
        '''Yum-metada orphan code'''
        path = AbstractOrphan.path + "/yum_repo_metadata_file/"


class OrphanFactory(Item):
    """to dispatch Orphans instantiation"""
    
    # type of orphan to instantiate is dependant on the
    # response's data['_content_type_id'] value
    type_map = {
        'rpm':                      RpmOrphan,
        RpmOrphan:                  'rpm',
        'distribution':             DistributionOrphan,
        DistributionOrphan:         'distribution',
        'drpm':                     DrpmOrphan,
        DrpmOrphan:                 'drpm',
        'erratum':                  ErratumOrphan,
        ErratumOrphan:              'erratum',
        'iso':                      IsoOrphan,
        IsoOrphan:                  'iso',
        'package_category':         PackageCategoryOrphan,
        PackageCategoryOrphan:      'package_category',
        'package_group':            PackageGroupOrphan,
        PackageGroupOrphan:         'package_group',
        'puppet_module':            PuppetModuleOrphan,
        PuppetModuleOrphan:         'puppet_module',
        'srpm':                     SrpmOrphan,
        SrpmOrphan:                 'srpm',
        'yum_repo_metadata_file':   YumRepoMetadataFileOrphan,
        YumRepoMetadataFileOrphan:  'yum_repo_metadata_file'  
    }
    path = AbstractOrphan.path
    
    @classmethod
    def from_data(cls, data):
        '''instantiate proper orphan type instances based on data'''
        if not isinstance(data, list):
            type_id = data['_content_type_id']
            # make sure there's type to instantiate to
            assert type_id in cls.type_map, "%s not found in type_map"\
                    % type_id
            return type_map[type_id](data)
        ret = []
        for item in items:
            type_id = data['_content_type_id']
            assert type_id in cls.type_map, "%s not found in type_map"\
                    % type_id
            ret.append(type_map[type_id](data))
        return ret

    @classmethod
    def from_response(cls, response):
        '''instantiate proper orphan item from a response'''
        data = response.json()
        return cls.from_data(data)

class Orphans(object):
    '''The content/orphans/ container handler'''
    path = '/content/orphans/'

    @classmethod
    def info(cls, pulp):
        return pulp.send(Request('GET', cls.path)).json()

    @classmethod
    def delete(cls, pulp):
        '''delete all orphans no matter the orphan type'''
        return pulp.send(Request('DELETE', cls.path))

    @classmethod
    def get(cls, pulp):
        '''get all orphans according to their type'''
        info = cls.info(pulp)
        ret = {}
        for orphan_type in info.keys():
            assert orphan_type in OrphanFactory.type_map, "Unknown orphan type: %s" % orphan_type
            ret[orphan_type] = OrphanFactory.type_map[orphan_type].list(pulp) 
        return ret

    
        
# introduce all required Orphan Subtypes
