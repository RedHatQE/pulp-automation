from unit import AbstractUnit, RpmUnit

class AbstractOrphan(AbstractUnit):
    """Orphans are Units just like the rest; only path differs. This is rather an abstract
    Orphan type"""
    path = '/content/orphans/'

class RpmOrphan(AbstractOrphan):
    '''rpm-specific orphan code'''
    path = AbstractOrphan.path + "/rpm/"
    
    # expand as needed
    relevant_data_keys = AbstractOrphan.relevant_data_keys + RpmUnit.relevant_data_keys


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
