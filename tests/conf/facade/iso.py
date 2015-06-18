"""
default iso pulp--role facades
"""

from generic import Repo, FeedImporter, WebDistributor


DEFAULT_FEED = 'https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/test_file_repo/'

class IsoDistributor(WebDistributor):
    def __init__(self, distributor_id='iso_distributor', distributor_type_id='iso_distributor',
                **kvs):
        super(IsoDistributor, self).__init__(distributor_id=distributor_id,
                distributor_type_id=distributor_type_id, **kvs)

    @classmethod
    def from_role(cls, repo):
        return super(IsoDistributor, cls).from_role(repo, distributor_id='iso_distributor',
                distributor_type_id='iso_distributor')


class IsoImporter(FeedImporter):
    def __init__(self, feed=DEFAULT_FEED, id='iso_importer', importer_type_id='iso_importer', **kvs):
        super(IsoImporter, self).__init__(feed=feed, id=id, importer_type_id=importer_type_id, **kvs)

    @classmethod
    def from_role(cls, repo):
        return super(IsoImporter, cls).from_role(repo, id='iso_importer',
                importer_type_id='iso_importer')


class IsoRepo(Repo):
    def __init__(self, notes={'_repo-type': 'iso-repo'}, **kvs):
        super(IsoRepo, self).__init__(notes=notes, **kvs)

    @classmethod
    def from_role(cls, repo):
        importer = IsoImporter.from_role(repo)
        distributors = [IsoDistributor.from_role(repo)]
        return super(IsoRepo, cls).from_role(repo, importer=importer, distributors=distributors)

