"""
default yum pulp--role facades
"""
from generic import Repo, FeedImporter, WebDistributor

DEFAULT_FEED = 'https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'

class YumDistributor(WebDistributor):
    def __init__(self, distributor_id='yum_distributor', distributor_type_id='yum_distributor',
                **kvs):
        super(YumDistributor, self).__init__(distributor_id=distributor_id,
                    distributor_type_id=distributor_type_id, **kvs)

    @classmethod
    def from_role(cls, repo):
        return super(YumDistributor, cls).from_role(repo, distributor_id='yum_distributor',
                                distributor_type_id='yum_distributor')


class YumImporter(FeedImporter):
    def __init__(self, feed=DEFAULT_FEED, id='yum_reporter', importer_type_id='yum_importer', **kvs):
        super(YumImporter, self).__init__(id=id, importer_type_id=importer_type_id, feed=feed, **kvs)

    @classmethod
    def from_role(cls, repo):
        return super(YumImporter, cls).from_role(repo, id='yum_importer', importer_type_id='yum_importer')


class YumRepo(Repo):

    def __init__(self, notes={'_repo-type': 'rpm-repo'}, **kvs):
        super(YumRepo, self).__init__(notes=notes, **kvs)

    @classmethod
    def from_role(cls, repo):
        importer = YumImporter.from_role(repo)
        distributors = [YumDistributor.from_role(repo)]
        return cls(id=repo.id, display_name=repo.get('display_name'),
                    description=repo.get('description'), importer=importer,
                    distributors=distributors)
