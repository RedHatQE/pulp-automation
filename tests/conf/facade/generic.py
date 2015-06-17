"""
generic facades
"""

from facade import Facade

class Importer(Facade):
    def __init__(self, id, importer_type_id, importer_config=dict()):
        self.id = id
        self.importer_type_id = importer_type_id
        self.importer_config = importer_config


    def as_data(self, **override):
        ret = dict(id=self.id, importer_type_id=self.importer_type_id,
                        importer_config=self.importer_config)
        ret.update(override)
        return ret

class FeedImporter(Importer):
    def __init__(self, id, importer_type_id, feed, proxy_host=None, proxy_port=None,
                    proxy_username=None, proxy_password=None, ssl_validation=False):
        super(FeedImporter, self).__init__(id, importer_type_id)
        self.importer_config.update(dict(feed=feed, ssl_validation=ssl_validation))
        if proxy_host is not None:
            if proxy_port is None:
                raise ValueError('proxy_host specified but proxy_port missing')
            self.importer_config.update(dict(proxy_host=proxy_host, proxy_port=proxy_port))
            if proxy_username is not None:
                if proxy_password is None:
                    raise ValueError('proxy_username specified but no proxy_password')
                self.importer_config.update(dict(proxy_username=proxy_username,
                            proxy_password=proxy_password))

    @classmethod
    def from_role(cls, repo, id, importer_type_id):
        # create FeedImporter; feed is mandatory attr of repo_role; proxy is optional
        ssl_validation = repo.get('ssl_validation', False)
        proxy_host, proxy_port, proxy_username, proxy_password = None, None, None, None
        proxy = repo.get('proxy')
        if proxy is not None:
            proxy_host = proxy.get('host')
            proxy_port = proxy.get('port')
            proxy_username = proxy.get('username')
            proxy_password = proxy.get('password')
        return cls(id=id, importer_type_id=importer_type_id, feed=repo.feed,
                    proxy_host=proxy_host, proxy_port=proxy_port, proxy_username=proxy_username,
                    proxy_password=proxy_password, ssl_validation=ssl_validation)

class Distributor(Facade):
    def __init__(self, distributor_id, distributor_type_id, auto_publish=False,
                    distributor_config=dict()):
        self.distributor_id = distributor_id
        self.distributor_type_id = distributor_type_id
        self.distributor_config = distributor_config
        self.auto_publish = auto_publish

    @classmethod
    def from_role(cls, repo, distributor_id, distributor_type_id):
        auto_publish = repo.get('auto_publish', False)
        return cls(distributor_id=distributor_id, distributor_type_id=distributor_type_id,
                    auto_publish=auto_publish)

    def as_data(self, **override):
        ret = dict(distributor_id=self.distributor_id, distributor_type_id=self.distributor_type_id,
                distributor_config=self.distributor_config, auto_publish=self.auto_publish)
        ret.update(override)
        return ret


class WebDistributor(Distributor):
    def __init__(self, distributor_id, distributor_type_id, auto_publish=False, http=True,
                    https=True, relative_url=None):
        super(WebDistributor, self).__init__(distributor_id=distributor_id,
                distributor_type_id=distributor_type_id, auto_publish=auto_publish)
        self.distributor_config.update(dict(http=http, https=https, relative_url=relative_url))

    @classmethod
    def from_role(cls, repo, distributor_id, distributor_type_id):
        relative_url = repo.get('relative_url', None)
        if relative_url is None:
            # relative url is mandatory; try figuring out of feed
            feed = repo.get('feed')
            if feed is None:
                raise ValueError('neither relative_url nor feed specified in %s' % repo)
            import urllib2
            relative_url = urllib2.urlparse.urlparse(feed).path
        return cls(distributor_id=distributor_id, distributor_type_id=distributor_type_id,
                    auto_publish=repo.get('auto_publish', False), http=repo.get('http', True),
                    https=repo.get('https', True), relative_url=relative_url)

class Repo(Facade):
    """base repo facade"""
    def __init__(self, id, display_name=None, description=None, importer=None, distributors=[]):
        self.id = id
        self.display_name = display_name
        self.description = description
        self.importer = importer
        self.distributors = distributors


    def create(self, pulp):
        """
        do repo create procedure with pulp,
        return created pulp-repo, -importer and [-distributors*] objects
        """
        from pulp_auto.repo import Repo as PulpRepo
        from pulp_auto.repo import Importer as PulpImporter
        from pulp_auto.repo import Distributor as PulpDistributor
        from pulp_auto.task import Task
        repo = PulpRepo(self.as_data())
        with pulp.asserting(True):
            repo = PulpRepo.from_response(repo.create(pulp))
            response = repo.associate_importer(pulp, data=self.importer.as_data())
            Task.wait_for_report(pulp, response)
            importer = repo.get_importer(pulp, self.importer.id)
            distributors = []
            for distributor in self.distributors:
                distributors.append(PulpDistributor.from_response(repo.associate_distributor(
                                        pulp, data=distributor.as_data())))
        return repo, importer, distributors

    def as_data(self, **override):
        ret = dict(id=self.id, display_name=self.display_name, description=self.description)
        ret.update(override)
        return ret

