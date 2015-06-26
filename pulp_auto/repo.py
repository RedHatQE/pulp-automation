import item, json
from pulp_auto import (Request, )
from . import (path_join, format_response, content_path, content_iso_path)
from pulp_auto.task import Task
from pulp_auto.item import ScheduledAction

NODE_DISTRIBUTOR_TYPE_ID='nodes_http_distributor'

class RepoAppl(object):
    path = '/repositories/'

    @staticmethod
    def applicability(
        pulp,
        data,
        path='/actions/content/regenerate_applicability/'
    ):
        path = path_join(RepoAppl.path, path)
        return pulp.send(Request('POST', path=path, data=data))

class Repo(item.Item):
    relevant_data_keys = ['id', 'display_name', 'description', 'notes']
    path = '/repositories/'

    def associate_importer(
        self,
        pulp,
        data,
        path='/importers/'
    ):
        return pulp.send(self.request('POST', path=path, data=data))

    def associate_distributor(
        self,
        pulp,
        data,
        path='/distributors/'
    ):
        return pulp.send(self.request('POST', path=path, data=data))

    def sync(
        self,
        pulp,
        data = {
            'override_config': {
            }
        },
        path='/actions/sync/'
    ):
        return pulp.send(self.request('POST', path=path, data=data))

    def get_sync_history(
        self,
        pulp,
        params={},
        path='/history/sync/'
    ):
        with pulp.asserting(True):
            response = pulp.send(self.request('GET', path=path, params=params))
        return response.json()

    def publish(
        self,
        pulp,
        distributor_id,
        config = None,
        path='/actions/publish/'
    ):
        data={
            'id': distributor_id,
            'override_config': config
        }
        return pulp.send(self.request('POST', path=path, data=data))

    def get_publish_history(
        self,
        pulp,
        dist_id,
        params={},
        path='/history/publish/'
    ):
        with pulp.asserting(True):
            response = pulp.send(self.request('GET', path_join(path, dist_id), params=params))
        return response.json()

    def list_importers(
        self,
        pulp,
    ):
        path = Importer.path
        with pulp.asserting(True):
            return pulp.send(self.request('GET', path=path)).json()

    def list_distributors(
        self,
        pulp,
    ):
        path = Distributor.path
        with pulp.asserting(True):
            return pulp.send(self.request('GET', path=path)).json()

    def get_importer(
        self,
        pulp,
        id,
    ):
        path = path_join(Importer.path, id)
        with pulp.asserting(True):
            return Importer.from_response(pulp.send(self.request('GET', path=path)))

    def get_distributor(
        self,
        pulp,
        id,
    ):
        path = path_join(Distributor.path, id)
        with pulp.asserting(True):
            return Distributor.from_response(pulp.send(self.request('GET', path=path)))

    def copy(
        self,
        pulp,
        source_repo_id,
        data={
            'override_config': {
                'resolve_dependencies': True,
                'recursive': True
            }
        },
        path='/actions/associate/'
    ):
        data.update({'source_repo_id': source_repo_id})
        return pulp.send(self.request('POST', path=path, data=data))


    def unassociate_units(
        self,
        pulp,
        data,
        path='/actions/unassociate/'
    ):
        # example of criteria usage
        # {"criteria": {"type_ids": ["puppet_module"], "filters": {"unit": {"name": "tomcat7_rhel"}}}}
        return pulp.send(self.request('POST', path=path, data=data))


    def within_repo_search(
        self,
        pulp,
        data,
        path='/search/units/'
    ):
        return pulp.send(self.request('POST', path=path, data=data))


class Importer(item.AssociatedItem):
    path = '/importers/'
    relevant_data_keys = ['id', 'importer_type_id', 'repo_id', 'config', 'last_sync']

    def schedule_sync(
        self,
        pulp,
        schedule,
        override_config=None
    ):
        data = {"override_config": override_config}
        return self.create_scheduled_action(pulp, action='/sync/', schedule=schedule, data=data)

    def get_scheduled_sync(
        self,
        pulp,
        id
    ):
        return self.get_scheduled_action(pulp, action='/sync/', id=id)

    def list_scheduled_sync(
        self,
        pulp,
    ):
        return self.list_scheduled_action(pulp, action='/sync/')

    def augment_proxy(self, pulp, host, port, username=None, password=None):
        """
        set proxy_ options
        """
        importer_config = dict(host=host, port=port)
        if username is not None:
            importer_config['proxy_username'] = username
        if password is not None:
            importer_config['proxy_password'] = password
        with pulp.asserting(True):
            pulp.send(self.request('PUT', data=dict(importer_config=importer_config)))
        self.reload(pulp)



class Distributor(item.AssociatedItem):
    path = '/distributors/'
    relevant_data_keys = ['id', 'distributor_type_id', 'repo_id', 'config', 'last_publish', 'auto_publish']

    def schedule_publish(
        self,
        pulp,
        schedule,
        override_config=None
    ):
        data = {"override_config": override_config}
        return self.create_scheduled_action(pulp, action='/publish/', schedule=schedule, data=data)

    def get_scheduled_publish(
        self,
        pulp,
        id
    ):
        return self.get_scheduled_action(pulp, action='/publish/', id=id)

    def list_scheduled_publish(
        self,
        pulp,
    ):
        return self.list_scheduled_action(pulp, action='/publish/')

    def content_url(self, pulp, path='/'):
        '''assemblel url of the content being served'''
        return path_join(pulp.url, content_path,
                self.data['config']['relative_url'], path).strip('/')

class IsoDistributor(Distributor):

    def content_url(self, pulp, path='/'):
        '''assemblel url of the content being served'''
        return path_join(pulp.url, content_iso_path,
                self.data['repo_id'], path).strip('/')

class NodeDistributor(Distributor):
    '''a node distributor'''
    # for convenience, default ID is set to the same as the type ID
    default_id = NODE_DISTRIBUTOR_TYPE_ID
    required_data_keys = ['id', 'distributor_type_id']

    @classmethod
    def default(cls, id=NODE_DISTRIBUTOR_TYPE_ID, config={}, auto_publish=False):

        '''default config constructor'''
        return cls(data=dict(id=id,
                            distributor_type_id=NODE_DISTRIBUTOR_TYPE_ID,
                            distributor_config=config, auto_publish=auto_publish))

class Association(item.AssociatedItem):
    path = '/search/units/'


def create_yum_repo(
    pulp,
    id,
    feed=None,
    display_name=None,
    relative_url=None,
    http=True,
    https=True,
    proxy=None,
    ssl_validation=False,
    **kvs
):
    '''create an almost default yum repo'''
    repo = Repo(
        {
            'id': id,
            'display_name': display_name,
            'notes': {"_repo-type": "rpm-repo"}
        }
    )
    if relative_url is None:
        relative_url = id
    importer_config = dict(feed=feed, ssl_validation=ssl_validation)
    if proxy is not None:
        proxy_importer(importer_config, **proxy)
    with pulp.asserting(True):
        #https://bugzilla.redhat.com/show_bug.cgi?id=1076225
        repo = Repo.from_response(repo.create(pulp))
        response = repo.associate_importer(
            pulp,
            data={
                'importer_type_id': 'yum_importer',
                'importer_id': 'yum_importer',
                'importer_config': importer_config,
            }
        )
        Task.wait_for_report(pulp, response)
        importer = repo.get_importer(pulp, "yum_importer")
        distributor = Distributor.from_response(repo.associate_distributor(
            pulp,
            data={
                'distributor_id': id + "_distributor",
                'distributor_type_id': 'yum_distributor',
                'distributor_config': {
                    'http': http,
                    'https': https,
                    'relative_url': relative_url
                },
                'auto_publish': False
            }
        ))
    return repo, importer, distributor


def create_puppet_repo(
    pulp,
    id,
    queries=[],
    feed='http://forge.puppetlabs.com',
    display_name=None,
    http=True,
    https=False,
    proxy=None
):

    '''create an almost default puppet repo'''
    repo = Repo(
         {
             'id': id,
             'display_name': display_name,
             'notes': {"_repo-type": "puppet-repo"}
         }
    )
    importer_config = dict(feed=feed, queries=queries)
    if proxy is not None:
        proxy_importer(importer_config, **proxy)
    with pulp.asserting(True):
        repo = Repo.from_response(repo.create(pulp))
        response = repo.associate_importer(
            pulp,
            data={
                'importer_type_id': 'puppet_importer',
                'importer_config': importer_config
            }
        )
        Task.wait_for_report(pulp, response)
        importer = repo.get_importer(pulp, "puppet_importer")
        distributor = Distributor.from_response(repo.associate_distributor(
            pulp,
            data={
                'distributor_id': id + "_distributor",
                'distributor_type_id': 'puppet_distributor',
                'distributor_config': {
                    'http': http,
                    'https': https
                },
                'auto_publish': False
            }
        ))
    return repo, importer, distributor

def proxy_importer(importer_data, host, port, username=None, password=None):
    """
    map proxy to importer config
    """
    importer_data['proxy_host'] = host
    importer_data['proxy_port'] = port
    if username is not None:
        if password is None:
            raise ValueError('username implies a password but None set')
        importer_data['proxy_username'] = username
        importer_data['proxy_password'] = password

def create_iso_repo(
    pulp,
    id,
    feed='http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/test_file_repo/',
    display_name=None,
    relative_url=None,
    http=True,
    https=True,
    proxy=None,
    **kvs
):
    '''create an almost default iso repo'''
    repo = Repo(
        {
            'id': id,
            'feed': feed,
            'display_name': display_name,
            'notes': {"_repo-type": "iso-repo"}
        }
    )
    if relative_url is None:
        relative_url = id
    importer_config = dict(feed=feed)
    if proxy is not None:
        proxy_importer(importer_config, **proxy)
    with pulp.asserting(True):
        repo = Repo.from_response(repo.create(pulp))
        response = repo.associate_importer(
            pulp,
            data={
                'importer_type_id': 'iso_importer',
                'importer_id': 'iso_importer',
                'importer_config': importer_config,
            }
        )
        Task.wait_for_report(pulp, response)
        importer = repo.get_importer(pulp, "iso_importer")
        distributor = IsoDistributor.from_response(repo.associate_distributor(
            pulp,
            data={
                'distributor_id': id + "_distributor",
                'distributor_type_id': 'iso_distributor',
                'distributor_config': {
                    'http': http,
                    'https': https,
                    'relative_url': relative_url
                },
                'auto_publish': False
            }
        ))
    return repo, importer, distributor

def create_docker_repo(
    pulp,
    id,
    feed='https://index.docker.io/',
    display_name=None,
    upstream_name='busybox',
    relative_url=None,
    http=True,
    https=True,
    proxy=None,
    **kvs
):
    '''create an almost default docker repo'''
    repo = Repo(
        {
            'id': id,
            'feed': feed,
            'display_name': display_name,
            'notes': {"_docker-type": "docker-repo"},
        }
    )
    importer_config = dict(feed=feed, upstream_name=upstream_name)
    if proxy is not None:
       proxy_importer(importer_config, **proxy)
    if relative_url is None:
        relative_url = id
    with pulp.asserting(True):
        repo = Repo.from_response(repo.create(pulp))
        response = repo.associate_importer(
            pulp,
            data={
                'importer_type_id': 'docker_importer',
                'importer_id': 'docker_importer',
                'importer_config': importer_config,
            }
        )
        Task.wait_for_report(pulp, response)
        importer = repo.get_importer(pulp, "docker_importer")
        distributor = Distributor.from_response(repo.associate_distributor(
            pulp,
            data={
                'distributor_id': id + "_distributor",
                'distributor_type_id': 'docker_distributor_web',
                'distributor_config': {
                    'http': http,
                    'https': https,
                    'relative_url': '/library/busybox'
                },
                'auto_publish': False
            }
        ))
    return repo, importer, distributor

SAMPLE_YUM_DISTRIBUTOR_CONFIG_DATA = {
    "distributor_id": "yum_distributor",
    "auto_publish": True,
    "distributor_type": "yum_distributor",
    "distributor_config": {
        "http": False,
        "https": True,
        "relative_url": "/repos/pulp/pulp/demo_repos/zoo/"
    }
}

SAMPLE_EXPORT_DISTRIBUTOR_CONFIG_DATA = {
    "distributor_id": "export_distributor",
    "auto_publish": False,
    "distributor_type": "export_distributor",
    "distributor_config": {
        "http": False,
        "https": True
    }
}

SAMPLE_YUM_DISTRIBUTOR_DATA = {
    "_id": {
        "$oid": "5257ef5cc805d066faef1d2f"
    },
    "_ns": "repo_distributors",
    "auto_publish": True,
    "config": {
        "http": False,
        "https": True,
        "relative_url": "/repos/pulp/pulp/demo_repos/zoo/"
    },
    "distributor_type_id": "yum_distributor",
    "id": "yum_distributor",
    "last_publish": "2013-10-11T13:06:32Z",
    "repo_id": "test_rpm_repo",
    "scheduled_publishes": [],
    "scratchpad": {}
}

SAMPLE_EXPORT_DISTRIBUTOR_DATA = {
    "_id": {
        "$oid": "5257ef5cc805d066faef1d30"
    },
    "_ns": "repo_distributors",
    "auto_publish": False,
    "config": {
    "http": False,
    "https": True
    },
    "distributor_type_id": "export_distributor",
    "id": "export_distributor",
    "last_publish": None,
    "repo_id": "test_rpm_repo",
    "scheduled_publishes": [],
    "scratchpad": None
}
