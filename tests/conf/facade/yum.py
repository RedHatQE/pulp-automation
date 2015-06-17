"""
default yum pulp--role facades
"""
from generic import Repo, FeedImporter, WebDistributor

class YumDistributor(WebDistributor):
    def __init__(self, distributor_id='yum_distributor', distributor_type_id='yum_distributor',
                    auto_publish=False, http=True, https=True, relative_url=None):
        super(YumDistributor, self).__init__(distributor_id=distributor_id,
                distributor_type_id=distributor_type_id, auto_publish=auto_publish, http=http,
                https=https, relative_url=relative_url)

    @classmethod
    def from_role(cls, repo):
        return super(YumDistributor, cls).from_role(repo, distributor_id='yum_distributor',
                                distributor_type_id='yum_distributor')


class YumImporter(FeedImporter):
    def __init__(self, feed, id='yum_reporter', importer_type_id='yum_importer', proxy_host=None,
                    proxy_port=None, proxy_username=None, proxy_password=None, ssl_validation=False):
        super(YumImporter, self).__init__(id=id, importer_type_id=importer_type_id, feed=feed,
                proxy_host=proxy_host, proxy_port=proxy_port, proxy_username=proxy_username,
                proxy_password=proxy_password, ssl_validation=False)

    @classmethod
    def from_role(cls, repo):
        return super(YumImporter, cls).from_role(repo, id='yum_importer', importer_type_id='yum_importer')


class YumRepo(Repo):
    @classmethod
    def from_role(cls, repo):
        importer = YumImporter.from_role(repo)
        distributors = [YumDistributor.from_role(repo)]
        return cls(id=repo.id, display_name=repo.get('display_name'),
                    description=repo.get('description'), importer=importer,
                    distributors=distributors)

    def as_data(self, **override):
        ret = super(YumRepo, self).as_data()
        ret['notes'] = {'_repo-type': 'rpm-repo'}
        ret.update(override)
        return ret
