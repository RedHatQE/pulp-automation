"""
default puppet pulp--role facades
"""

from generic import Repo, FeedImporter, WebDistributor

class PuppetDistributor(WebDistributor):
    def __init__(self, distributor_id='puppet_distributor', distributor_type_id='puppet_distributor',
                    auto_publish=False, http=True, https=True, relative_url=None):
            super(PuppetDistributor, self).__init__(distributor_id=distributor_id,
                    distributor_type_id=distributor_type_id, auto_publish=auto_publish, http=http,
                    https=https, relative_url=relative_url)

    @classmethod
    def from_role(cls, repo):
        return super(PuppetDistributor, cls).from_role(repo, distributor_id='puppet_distributor',
                        distributor_type_id='puppet_distributor')


class PuppetImporter(FeedImporter):
    def __init__(self, feed='http://forge.puppetlabs.com', id='puppet_importer',
                    importer_type_id='puppet_importer', proxy_host=None, proxy_port=None,
                    proxy_username=None, proxy_password=None, ssl_validation=False, queries=[]):
        super(PuppetImporter, self).__init__(feed=feed, id=id,
                    importer_type_id=importer_type_id, proxy_host=proxy_host, proxy_port=proxy_port,
                    proxy_username=proxy_username, proxy_password=proxy_password,
                    ssl_validation=ssl_validation)
        self.importer_config['queries'] = queries

    @classmethod
    def from_role(cls, repo):
        queries = repo.get('queries', [])
        ret = super(PuppetImporter, cls).from_role(repo, id='puppet_importer',
                    importer_type_id='puppet_importer')
        ret.importer_config['queries'] = queries
        return ret



class PuppetRepo(Repo):

    @classmethod
    def from_role(cls, repo):
        importer = PuppetImporter.from_role(repo)
        distributors = [PuppetDistributor.from_role(repo)]
        return cls(id=repo['id'], display_name=repo.get('display_name'),
                    description=repo.get('description'), importer=importer,
                    distributors=distributors)

    def as_data(self, **override):
        ret = super(PuppetRepo, self).as_data()
        ret['notes'] = {'_repo-type': 'puppet-repo'}
        ret.update(override)
        return ret
