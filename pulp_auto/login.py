import requests
from . import (path as pulp_path, normalize_url)

path = normalize_url(pulp_path + '/actions/login/')


def request():
    return lambda url, auth: requests.Request('POST', normalize_url(url + path), auth=auth).prepare()
