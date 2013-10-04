# top-level stuff

path='/pulp/api/v2/'

def normalize_url(url):
    '''remove stacked forward slashes'''
    import re
    return re.sub('([^:])///*', r'\1/', url)

def path_join(*args):
    '''combine args into a path with a trailing /'''
    return '/'.join(args) + '/'

from pulp import (Pulp, Request, format_response)
import item, repo, namespace, importer, hasdata
