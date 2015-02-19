from tests.pulp_test import PulpTest, deleting, temp_url
from pulp_auto.upload import Upload, rpm_metadata
from pulp_auto.repo import create_yum_repo
from pulp_auto.task import Task
from contextlib import closing

# We want this test to download using dnf, no point to continue if there is no dnf
try:
    import dnf
except ImportError as e:
    import unittest
    raise unittest.SkipTest(e)

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

class DownloadContentTest(PulpTest):
    rpm_url = 'https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/bear-4.1-1.noarch.rpm'
    def testcase_01_upload_and_download_using_dnf_rpm(self):
        # create yum-repo, -importer, -distributor
        with deleting(self.pulp, *create_yum_repo(self.pulp, 'test_22_rpm_repo_for_dnf')) as (repo, (importer, (distributor))):
            # create and perform an rpm url upload
            with deleting(self.pulp, upload_url_rpm(self.pulp, self.rpm_url)) as upload:
                # assign the upload to the repo
                response = upload.import_to(self.pulp, repo)
                self.assertPulpOK()
                Task.wait_for_report(self.pulp, response)
                # check the content is accessible
                response = repo.publish(self.pulp, distributor.id)
                self.assertPulpOK()
                Task.wait_for_report(self.pulp, response)
                # fetch the package through the repo
                pulp_rpm_url = distributor.content_url(self.pulp, url_basename(self.rpm_url))
                pulp_repo = distributor.content_url(self.pulp)
                with closing(temp_url(pulp_rpm_url)) as tmpfile:
                    assert url_basename(self.rpm_url).startswith(rpm_metadata(tmpfile)['unit_key']['name'])
                assert "bear" == download_package_with_dnf(self.pulp, pulp_repo, "bear")

