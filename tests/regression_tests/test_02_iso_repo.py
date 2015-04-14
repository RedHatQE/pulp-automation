from pulp_auto.consumer import (Cli, RpmUnit, YumRepo, RpmRepo, Consumer)
from pulp_auto.task import (Task, TaskFailure)
from pulp_auto.units import Orphans
from pulp_auto.repo import create_iso_repo, Repo, Importer, Distributor
from tests.pulp_test import PulpTest, requires_any, deleting
from tests.utils.upload import upload_url_iso,iso_metadata, temp_url, url_basename
from tests import ROLES
from contextlib import closing


def setUpModule():
    pass

def tearDownModule():
    pass

class IsoRepoTest(PulpTest):
    
    iso_url_test = "https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/test_file_repo/test.iso"

    @classmethod
    def setUpClass(cls):
        super(IsoRepoTest, cls).setUpClass()

        cls.repo, cls.importer1, cls.distributor1 = create_iso_repo(cls.pulp, cls.__name__ + "_repo", feed='https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/test_file_repo/')

        cls.repo_copy, cls.importer_copy, cls.distributor_copy = create_iso_repo(cls.pulp, cls.__name__ + "_repo_copy", feed=None)

        cls.repo_upload, cls.importer_upload, cls.distributor_upload = create_iso_repo(cls.pulp, cls.__name__ + "_repo_upload", feed=None)


    @classmethod
    def tearDownClass(cls):
        super(IsoRepoTest, cls).tearDownClass()

        # delete repos
        with cls.pulp.asserting(True):
            response = cls.repo.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, response)
        
        with cls.pulp.asserting(True):
            response = cls.repo_copy.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, response)

        with cls.pulp.asserting(True):
            response = cls.repo_upload.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, response)


    def test_01_sync_repo_and_publish(self):
        with self.pulp.asserting(True):
            response = self.repo.sync(self.pulp)
        Task.wait_for_report(self.pulp, response)

        with self.pulp.asserting(True):        
            response = self.repo.publish(self.pulp, self.distributor1.id)
        Task.wait_for_report(self.pulp, response)        

    def test_02_copy_repo_to_repo_copy_and_publish(self):
        with self.pulp.asserting(True):
            response = self.repo_copy.copy(self.pulp, self.repo.id, data={})
        Task.wait_for_report(self.pulp, response)
        
        #check that the number of modules are the same
        repo = Repo.get(self.pulp, self.repo.id)
        repo_copy = Repo.get(self.pulp, self.repo_copy.id)
        self.assertEqual(repo.data['content_unit_counts'], repo_copy.data['content_unit_counts'])

        with self.pulp.asserting(True):        
            response = self.repo_copy.publish(self.pulp, self.distributor_copy.id)
        Task.wait_for_report(self.pulp, response)        

    def test_03_upload_to_repo_upload_and_publish(self):

        def iso_uploader(pulp, url, repo, distributor):
            '''perform an upload'''
            # create an already fed upload object
            with deleting(pulp, upload_url_iso(pulp, url)) as upload:
                # upload = upload_url_iso(pulp, url)
                # assing upload to repo
                Task.wait_for_report(pulp, upload.import_to(pulp, repo))
                # publish the content
                Task.wait_for_report(pulp, repo.publish(pulp, distributor.id))
                # download the rpm from pulp now
                pulp_iso_url = distributor.content_url(pulp, url_basename(url))
                with closing(temp_url(pulp_iso_url)) as tmpfile:
                # make sure the iso fetched has the same name as the one uploaded
                # FIXME: asilly check indeed ;)
                    # print "============================================================"
                    # print url_basename(url)
                    # print url
                    # print pulp_iso_url
                    # print iso_metadata(tmpfile)['unit_key']['name']
                    # print "============================================================"
                # import pprint
                # print pprint.pformat(distributor.data)
                    assert upload.data['unit_key']['checksum'].startswith(iso_metadata(tmpfile)['unit_key']['checksum'])

        iso_uploader(self.pulp, self.iso_url_test, self.repo_upload, self.distributor_upload)
