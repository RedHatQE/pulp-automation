"""
common upload utils
"""
from contextlib import closing
from pulp_auto.upload import Upload, rpm_metadata
from pulp_auto.repo import Repo, Distributor
import dnf

def temp_url(url, chunksize=65535):
    '''save the url as a temporary named file object'''
    import tempfile
    import urllib2
    fd = urllib2.urlopen(url)
    tmpfd = tempfile.NamedTemporaryFile()
    while True:
        data = fd.read(chunksize)
        if not data:
            break
        tmpfd.write(data)
    tmpfd.file.seek(0)
    fd.close()
    return tmpfd

def url_basename(url):
    '''basename from url'''
    import os
    import urllib2
    return os.path.basename(urllib2.urlparse.urlsplit(url).path)

def upload_url_rpm(pulp, url):
    '''create an upload object fed from the url'''
    # get basename for upload purpose
    basename = url_basename(url)
    with closing(temp_url(url)) as tmpfile:
        data = rpm_metadata(tmpfile.file)
        # augment rpm file name
        data['unit_metadata']['relativepath'] = basename
        data['unit_metadata']['filename'] = basename
        upload = Upload.create(pulp, data=data)
        # feed the data
        tmpfile.file.seek(0)
        upload.file(pulp, tmpfile.file)
    return upload

def download_package_with_dnf(pulp, repo_url, package_name):
    base = dnf.Base()
    conf = base.conf
    conf.cachedir = '/tmp/download_package_with_dnf_1' 
    conf.substitutions['releasever'] = '22'
    repo = dnf.repo.Repo('ZooInPulp', conf.cachedir)
    repo.baseurl = repo_url
    repo.sslverify = False
    repo.load()
    base.repos.add(repo)
    base.fill_sack()
    query = base.sack.query()
    available = query.available()
    available = available.filter(name=package_name)
    base.download_packages(available)
    package = available[0]
    return package.name

def pulp_repo_url(pulp, repo_id, distributor_type_id='yum_distributor'):
    '''return repo content url for given repo id or None'''
    repo = Repo.get(pulp, repo_id)
    # this should at most 1 item (for any given type)
    distributors = [distributor for distributor in repo.list_distributors(pulp) \
        if distributor['distributor_type_id'] == distributor_type_id]
    if not distributors:
        return None
    return Distributor(data=distributors[0]).content_url(pulp)
