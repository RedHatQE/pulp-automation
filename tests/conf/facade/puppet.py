"""
default puppet pulp--role facades
"""

from generic import Repo, FeedImporter, WebDistributor

DEFAULT_FEED = 'https://forge.puppetlabs.com'

class PuppetDistributor(WebDistributor):
    def __init__(self, distributor_id='puppet_distributor', distributor_type_id='puppet_distributor',
                    **kvs):
            super(PuppetDistributor, self).__init__(distributor_id=distributor_id,
                    distributor_type_id=distributor_type_id, **kvs)

    @classmethod
    def from_role(cls, repo):
        return super(PuppetDistributor, cls).from_role(repo, distributor_id='puppet_distributor',
                        distributor_type_id='puppet_distributor')


class PuppetImporter(FeedImporter):
    def __init__(self, feed=DEFAULT_FEED, id='puppet_importer', importer_type_id='puppet_importer',
                    queries=[], **kvs):
        super(PuppetImporter, self).__init__(feed=feed, id=id, importer_type_id=importer_type_id,
                    **kvs)
        self.importer_config['queries'] = queries

    @classmethod
    def from_role(cls, repo):
        queries = repo.get('queries', [])
        ret = super(PuppetImporter, cls).from_role(repo, id='puppet_importer',
                    importer_type_id='puppet_importer')
        ret.importer_config['queries'] = queries
        return ret



class PuppetRepo(Repo):

    def __init__(self, notes={'_repo-type': 'puppet-repo'}, **kvs):
        super(PuppetRepo, self).__init__(notes=notes, **kvs)

    @classmethod
    def from_role(cls, repo):
        importer = PuppetImporter.from_role(repo)
        distributors = [PuppetDistributor.from_role(repo)]
        return cls(id=repo['id'], display_name=repo.get('display_name'),
                    description=repo.get('description'), importer=importer,
                    distributors=distributors)
