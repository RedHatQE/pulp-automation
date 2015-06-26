"""
default docker pulp--role facades
"""
from generic import Repo, FeedImporter, WebDistributor

DEFAULT_FEED = 'https://index.docker.io/'

class DockerDistributor(WebDistributor):
    def __init__(self, distributor_id='docker_distributor',
                distributor_type_id='docker_distributor_web', **kvs):
        super(DockerDistributor, self).__init__(distributor_id=distributor_id,
                distributor_type_id=distributor_type_id, **kvs)

    @classmethod
    def from_role(cls, repo):
        return super(DockerDistributor, cls).from_role(repo, distributor_id='docker_distributor',
                distributor_type_id='docker_distributor_web')


class DockerImporter(FeedImporter):
    def __init__(self, upstream_name, feed=DEFAULT_FEED, id='docker_importer',
                importer_type_id='docker_importer', **kvs):
        super(DockerImporter, self).__init__(feed=feed, id=id, importer_type_id=importer_type_id,
                **kvs)
        self.importer_config['upstream_name'] = upstream_name

    @classmethod
    def from_role(cls, repo):
        upstream_name = repo.get('upstream_name')
        if upstream_name is None:
            raise ValueError('Docker importer requires upstream name, None given')
        ret = super(DockerImporter, cls).from_role(repo, upstream_name=upstream_name,
                id='docker_importer', importer_type_id='docker_importer')
        ret.importer_config['upstream_name'] = upstream_name
        return ret


class DockerRepo(Repo):
    def __ini__(self, notes={'_repo-type': 'docker-repo'}, **kvs):
        super(DockerRepo, self).__init__(notes=notes, **kvs)

    @classmethod
    def from_role(cls, repo):
        importer = DockerImporter.from_role(repo)
        distributors = [DockerDistributor.from_role(repo)]
        return super(DockerRepo, cls).from_role(repo, importer=importer, distributors=distributors)
