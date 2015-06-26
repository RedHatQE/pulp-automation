from tests.pulp_test import PulpTest, deleting
from pulp_auto.upload import Upload, rpm_metadata
from pulp_auto.task import Task
from contextlib import closing
from tests.utils.upload import temp_url, url_basename, upload_url_rpm, download_package_with_dnf
from tests.conf.facade.yum import YumRepo, YumImporter, YumDistributor

# We want this test to download using dnf, no point to continue if there is no dnf
try:
    import dnf
except ImportError as e:
    import unittest
    raise unittest.SkipTest(e)

class DownloadContentTest(PulpTest):
    rpm_url = 'https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/bear-4.1-1.noarch.rpm'
    def testcase_01_upload_and_download_using_dnf_rpm(self):
        # create yum-repo, -importer, -distributor
        repo, importer, [distributor] = YumRepo(id='test_22_rpm_repo_for_dnf', importer=YumImporter(feed=None),
                                            distributors=[YumDistributor(relative_url='xyz')]).create(self.pulp)
        with deleting(self.pulp, repo, importer, distributor):
            # create and perform an rpm url upload
            with deleting(self.pulp, upload_url_rpm(self.pulp, self.rpm_url)) as (upload,):
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

