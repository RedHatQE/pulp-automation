from tests.pulp_test import PulpTest, deleting
from pulp_auto.upload import Upload, rpm_metadata
from pulp_auto.repo import create_yum_repo
from pulp_auto.task import Task
from tests.utils.upload import upload_url_rpm, temp_url, url_basename
from contextlib import closing


class UploadCudTest(PulpTest):
    rpm_url_bear = 'https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/bear-4.1-1.noarch.rpm'
    rpm_url_mouse = 'https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/mouse-0.1.12-1.noarch.rpm'

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

    @staticmethod
    def rpm_uploader(pulp, url, repo, distributor):
        '''perform an upload'''
        # create an already fed upload object
        with deleting(pulp, upload_url_rpm(pulp, url)) as upload:
            # assing upload to repo
            Task.wait_for_report(pulp, upload.import_to(pulp, repo))
            # publish the content
            Task.wait_for_report(pulp, repo.publish(pulp, distributor.id))
            # download the rpm from pulp now
            pulp_rpm_url = distributor.content_url(pulp, url_basename(url))
            with closing(temp_url(pulp_rpm_url)) as tmpfile:
                # make sure the rpm fetched has the same name as the one uploaded
                # rpm.name == 'bear' FIXME: a silly check indeed ;)
                assert url_basename(url).startswith(rpm_metadata(tmpfile)['unit_key']['name'])


    def testcase_02_upload_rpm(self):
        # create yum-repo, -importer, -distributor
        with deleting(self.pulp, *create_yum_repo(self.pulp, 'upload_test_rpm_repo')) as (repo, (importer, (distributor))):
            # create and perform an rpm url upload
            self.rpm_uploader(self.pulp, self.rpm_url_bear, repo, distributor)

    def testcase_03_parallel_upload_rpms(self):
        import gevent
        with deleting(self.pulp, *create_yum_repo(self.pulp, 'upload_test_rpm_repo')) as (repo, (importer, (distributor))):
            # create and perform an rpm url upload
            jobs = [gevent.spawn(lambda: self.rpm_uploader(self.pulp, url, repo, distributor)) for url in \
                            [self.rpm_url_bear, self.rpm_url_mouse]]
            gevent.joinall(jobs, raise_error=True)
