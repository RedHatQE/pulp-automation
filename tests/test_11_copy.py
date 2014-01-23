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
        # prepare repos
        feed = None
        feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'
        dest_repo = cls.__name__ + '_copy'
        repo1 = Repo({'id': dest_repo})
        repo1.delete(cls.pulp)
        cls.repo1 = create_yum_repo(cls.pulp, dest_repo, feed, relative_url=dest_repo)[0]
        feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'
        source_repo =  cls.__name__ + '_repo'
        repo2 = Repo({'id': source_repo})
        repo2.delete(cls.pulp)
        cls.repo2 = create_yum_repo(cls.pulp, source_repo, feed, relative_url=dest_repo)[0]
        sync_task = Task.from_response(cls.repo2.sync(cls.pulp))[0]
        sync_task.wait(cls.pulp)
        #repo2.sync(cls.pulp)



    def test_1_copy_repo(self):

        source_repo = self.repo2.id
        response = self.repo1.copy(
            self.pulp,
            data={
                'source_repo_id': source_repo
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

