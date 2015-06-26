from pulp_auto.consumer import (Cli, RpmUnit, YumRepo, RpmRepo, Consumer)
from pulp_auto.task import (Task, TaskFailure)
from pulp_auto.units import Orphans
from pulp_auto.upload import Upload, rpm_metadata
from pulp_auto.repo import Repo, Importer, Distributor
from tests.pulp_test import (PulpTest, requires_any, deleting)
from tests.utils.upload import upload_url_rpm, temp_url, url_basename
from tests.conf.roles import ROLES
from tests.conf.facade.yum import YumRepo as YumRepoFacade, YumImporter, YumDistributor
from contextlib import closing

def setUpModule():
    pass

def tearDownModule():
    pass

@requires_any('consumers')
class RegRepoNoFeedTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RegRepoNoFeedTest, cls).setUpClass()

        # create repo
        cls.repo, cls.importer, [cls.distributor] = YumRepoFacade(id=cls.__name__ + "_repo",
                    importer=YumImporter(feed=None),
                    distributors=[YumDistributor(relative_url='foo')]).create(cls.pulp)

        # create consumer
        cls.consumer = Consumer(ROLES.consumers[0])
        setattr(cls.consumer, 'cli', Cli.ready_instance(**ROLES.consumers[0]))

        # rpm
        cls.rpm_url_pike = 'https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/pike-2.2-1.noarch.rpm'


    @staticmethod
    def rpm_uploader(pulp, url, repo, distributor):
        '''perform an upload'''
        # create an already fed upload object
        with deleting(pulp, upload_url_rpm(pulp, url)) as (upload,):
            # assing upload to repo
            Task.wait_for_report(pulp, upload.import_to(pulp, repo))
            # publish the content
            Task.wait_for_report(pulp, repo.publish(pulp, distributor.id))
            # download the rpm from pulp now
            pulp_rpm_url = distributor.content_url(pulp, url_basename(url))
            with closing(temp_url(pulp_rpm_url)) as tmpfile:
                # make sure the rpm fetched has the same name as the one uploaded
                assert url_basename(url).startswith(rpm_metadata(tmpfile)['unit_key']['name'])

    def test_01_upload_rpm(self):
        # create and perform an rpm url upload
        self.rpm_uploader(self.pulp, self.rpm_url_pike, self.repo, self.distributor)

    def test_02_publish_repo(self):
        with self.pulp.asserting(True):
            response = self.repo.publish(self.pulp, self.distributor.id)
        Task.wait_for_report(self.pulp, response)

    def test_03_api_registered_consumer(self):
        # assert the cli registration worked in API
        with self.pulp.asserting(True):
            Consumer.get(self.pulp, self.consumer.cli.consumer_id)

    def test_04_bind_distributor(self):
        with self.pulp.asserting(True):
           response = self.consumer.bind_distributor(self.pulp, self.repo.id, self.distributor.id)
        Task.wait_for_report(self.pulp, response)

    def test_05_assert_yum_repos(self):
        remote_yum_repo = YumRepo.list(self.consumer.cli)
        self.assertIn(YumRepo({'id': self.repo.id}), remote_yum_repo)

    def test_06_assert_unit_install(self):
        unit = {
            'name': 'pike'
        }
        rpm = RpmUnit(unit, relevant_data_keys=unit.keys())
        with self.pulp.asserting(True):
            response = self.consumer.install_unit(self.pulp, unit, 'rpm')
        Task.wait_for_report(self.pulp, response)
        assert rpm in RpmUnit.list(self.consumer.cli), "rpm %s not installed on %s" % (rpm, self.consumer)

    def test_07_assert_unit_uninstall(self):
        unit = {
            'name': 'pike'
        }
        rpm = RpmUnit(unit, relevant_data_keys=unit.keys())
        assert rpm in RpmUnit.list(self.consumer.cli), "rpm %s not installed on %s" % (rpm, self.consumer)
        with self.pulp.asserting(True):
            response = self.consumer.uninstall_unit(self.pulp, unit, 'rpm')
        Task.wait_for_report(self.pulp, response)
        assert rpm not in RpmUnit.list(self.consumer.cli), "rpm %s still installed on %s" % (rpm, self.consumer)

    def test_08_unbind_repo(self):
        with self.pulp.asserting(True):
            response = self.consumer.unbind_distributor(self.pulp, self.repo.id, self.distributor.id)
        Task.wait_for_report(self.pulp, response)

    @classmethod
    def tearDownClass(cls):
        # delete repo
        with cls.pulp.asserting(True):
            response = cls.repo.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, response)

        # delete orphans
        with cls.pulp.asserting(True):
            response = Orphans.delete(cls.pulp)
        Task.wait_for_report(cls.pulp, response)

        # unregister consumer
        cls.consumer.cli.unregister()
        super(RegRepoNoFeedTest, cls).tearDownClass()
