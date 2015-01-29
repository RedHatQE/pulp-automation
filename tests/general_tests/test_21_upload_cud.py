from tests.pulp_test import PulpTest, deleting, temp_url
from pulp_auto.upload import Upload, rpm_metadata
from pulp_auto.repo import create_yum_repo
from pulp_auto.task import Task
from contextlib import closing

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
        # create yum-repo, -importer, -distributor
        with deleting(self.pulp, *create_yum_repo(self.pulp, 'upload_test_rpm_repo')) as (repo, (importer, (distributor))):
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
                with closing(temp_url(pulp_rpm_url)) as tmpfile:
                    # make sure the rpm fetched has the same name as the one uploaded
                    # rpm.name == 'bear' FIXME: a silly check indeed ;)
                    assert url_basename(self.rpm_url).startswith(rpm_metadata(tmpfile)['unit_key']['name'])

