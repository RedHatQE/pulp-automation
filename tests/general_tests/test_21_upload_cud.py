from tests.pulp_test import PulpTest, deleting
from pulp_auto.upload import Upload, rpm_metadata
from pulp_auto.repo import create_yum_repo
from pulp_auto.task import Task
from contextlib import contextmanager
import urllib2

@contextmanager
def tmpurl_ctx(url, chunksize=65536):
    '''save the url as a temporary named file object'''
    import tempfile
    fd = urllib2.urlopen(url)
    tmpfd = tempfile.NamedTemporaryFile()
    while True:
        data = fd.read(chunksize)
        if not data:
            break
        tmpfd.write(data)
    tmpfd.file.seek(0)
    fd.close()
    try:
        yield tmpfd
    finally:
        tmpfd.close()

def upload_url_rpm(pulp, url):
    '''create an upload object fed from the url'''
    import os
    # get basename for upload purpose
    basename = os.path.basename(urllib2.urlparse.urlsplit(url).path)
    with tmpurl_ctx(url) as tmpfile:
        data = rpm_metadata(tmpfile.file)
        # augment rpm file name
        data['unit_metadata']['relativepath'] = basename
        data['unit_metadata']['filename'] = basename
        upload = Upload.create(pulp, data=data)
        # feed the data
        tmpfile.file.seek(0)
        upload.file(pulp, tmpfile.file)
    return upload

class UploadCudTest(PulpTest):
    rpm_url = 'https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/bear-4.1-1.noarch.rpm'
    def testcase_01_create_delete_upload(self):
        '''test creating uploads works'''
        upload = Upload.create(self.pulp)
        # assert what was created is what is kept locally
        ids = Upload.list(self.pulp)
        assert upload.id in ids, 'could not find id %s on server (%s)' % (upload.id, ids)
        # assert GET doesn't work
        with self.assertRaises(TypeError):
            Upload.get(self.pulp, upload.id)

        # assert deleting works
        upload.delete(self.pulp)
        self.assertPulpOK()
        ids = Upload.list(self.pulp)
        assert upload.id not in ids, 'upload %s deleted but still on server (%s)' % (upload.id, ids)

    def testcase_02_upload_rpm(self):
        with deleting(self.pulp, create_yum_repo(self.pulp, 'upload_test_rpm_repo')[0]) as repo:
            with deleting(self.pulp, upload_url_rpm(self.pulp, self.rpm_url)) as upload:
                response = upload.import_to(self.pulp, repo)
                self.assertPulpOK()
                Task.wait_for_report(self.pulp, response)

