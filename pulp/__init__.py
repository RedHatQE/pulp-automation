# top-level stuff

path='/pulp/api/v2/'

def normalize_url(url):
    '''remove stacked forward slashes'''
    import re
    return re.sub('([^:])///*', r'\1/', url)


from pulp import (Pulp, Request)
import item, repo, namespace
