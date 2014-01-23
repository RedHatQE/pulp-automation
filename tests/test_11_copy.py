import pulp_test, json, pulp_auto
from pulp_auto.repo import Repo, Importer, Distributor, create_yum_repo
from pulp_auto.task import Task, GroupTask 
 
def setUpModule():
    pass


"""class RepoTest(pulp_test.PulpTest):
    @classmethod
    def setUpClass(cls):
        super(RepoTest, cls).setUpClass()
        cls.repo = Repo(data={'id': cls.__name__ + "_repo"})
        cls.feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'"""


class SimpleRepoCopyTest(pulp_test.PulpTest):

    @classmethod
    def setUpClass(cls):
        super(SimpleRepoCopyTest, cls).setUpClass()
        #Destination repo
        feed = None
        dest_repo_name = cls.__name__ + '_copy'
        dest_repo1 = Repo({'id': dest_repo_name})
        dest_repo1.delete(cls.pulp)
        cls.dest_repo1 = create_yum_repo(cls.pulp, dest_repo_name, feed, relative_url=dest_repo_name)[0]

        #2nd Destination Repo
        dest_repo_name = cls.__name__ + '_copy1'
        dest_repo2 = Repo({'id': dest_repo_name})
        dest_repo2.delete(cls.pulp)
        cls.dest_repo2 = create_yum_repo(cls.pulp, dest_repo_name, feed, relative_url=dest_repo_name)[0]

        # Source repo
        feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'
        source_repo_name =  cls.__name__ + '_repo'
        source_repo = Repo({'id': source_repo_name})
        source_repo.delete(cls.pulp)
        cls.source_repo = create_yum_repo(cls.pulp, source_repo_name, feed, relative_url=source_repo_name)[0]
        sync_task = Task.from_response(cls.source_repo.sync(cls.pulp))[0]
        sync_task.wait(cls.pulp)


    def test_1_copy_repo_all(self):

        source_repo = self.source_repo.id
        response = self.dest_repo1.copy(
            self.pulp,
            data={
                'source_repo_id': source_repo
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)


    @classmethod
    def tearDownClass(cls):
        pass

