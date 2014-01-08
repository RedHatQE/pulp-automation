# top-level stuff
from gevent import monkey; monkey.patch_all()

path='/pulp/api/v2/'

def normalize_url(url):
    '''remove stacked forward slashes'''
    import re
    return re.sub('([^:])///*', r'\1/', url)

def strip_url(url):
    '''remove the url host and path prefix'''
    import urllib
    return normalize_url('/' + "/".join((urllib.splithost(urllib.splittype(url)[1])[1]).split(path)[1:]) + '/')

def path_join(*args):
    '''combine args into a path with a trailing /'''
    return normalize_url('/'.join(args) + '/')

def path_split(path):
    return normalize_url(path).split('/')


from pulp import (Pulp, Request, ResponseLike, format_response, format_preprequest)
import item, repo, namespace, hasdata, qpid_handle, consumer, agent, permission, handler, orphan
