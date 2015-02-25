from unit import (AbstractUnit, RpmUnit, UnitFactory)
from pulp_auto.pulp import Request


class AbstractOrphan(AbstractUnit):
    """Orphans are Units just like the rest; only path differs. This is rather an abstract
    Orphan type"""
    path = '/content/orphans/'

    @classmethod
    def delete_all(cls, pulp):
        '''delete all orphans of particular type in pulp instance'''
        return pulp.send(Request('DELETE', cls.path))


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

class PackageEnvironmentOrphan(AbstractOrphan):
    ''' package environments (collections of package groups) orphan code'''
    path = AbstractOrphan.path + "/package_environment/"


class DockerOrphan(AbstractOrphan):
    '''docker-specific orphan code'''
    path = AbstractOrphan.path + "/docker_image/"

#Nodes and repositories leaked from pulp-nodes into pulp-server 2.6.0-7 - this will be fixed in 2.6.1
class NodeOrphan(AbstractOrphan):
    path = AbstractOrphan.path + "/node/"

class RepositoryOrphan(AbstractOrphan):
    path = AbstractOrphan.path + "/repository/"
# End of workaround


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
            assert orphan_type in UnitFactory.type_map.orphans, "Unknown orphan type: %s" % orphan_type
            ret[orphan_type] = UnitFactory.type_map.orphans[orphan_type].list(pulp)
        return ret

    @classmethod
    def delete_by_type_id(
        cls,
        pulp,
        data,
        path='/content/actions/delete_orphans/'
    ):
        return pulp.send(Request('POST', path=path, data=data))


    
# introduce all required Orphan Subtypes
