# top-level stuff
from gevent import monkey; monkey.patch_all(aggressive=False, select=True)
# automation env doesn't care much about the warnings being displayed immediatelly
import logging; logging.captureWarnings(True)

path = '/pulp/api/v2/'
static_path = '/pulp/static/'
content_path = '/pulp/repos/'
content_iso_path = '/pulp/isos/'

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

def path_fields(path):
    '''because the leading and terminating slashes give ["",... , ""] when path is split'''
    return path_split(path)[1:-1]

def path_last(path):
    return path_fields[-1]


from pulp import (Pulp, Request, ResponseLike, format_response, format_preprequest)
import item, repo, namespace, hasdata, qpid_handle, consumer, agent, permission, handler, units, upload, event_listener, node
