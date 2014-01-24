import pulp_test, json, pulp_auto
from pulp_auto.repo import Repo, Importer, Distributor, create_yum_repo
from pulp_auto.task import Task, GroupTask 
 
def setUpModule():
    pass



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

    def test_2_copy_rpm(self):

        source_repo = self.source_repo.id
        response = self.dest_repo2.copy(
            self.pulp,
            data={
                'source_repo_id': source_repo,
                'criteria': {
                'type_ids': ['rpm']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_3_copy_category(self):

        source_repo = self.source_repo.id
        response = self.dest_repo2.copy(
            self.pulp,
            data={
                'source_repo_id': source_repo,
                'criteria': {
                'type_ids': ['package_category']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)


    def test_4_copy_group(self):

        source_repo = self.source_repo.id
        response = self.dest_repo2.copy(
            self.pulp,
            data={
                'source_repo_id': source_repo,
                'criteria': {
                'type_ids': ['package_group']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_4_copy_distribution(self):

        source_repo = self.source_repo.id
        response = self.dest_repo2.copy(
            self.pulp,
            data={
                'source_repo_id': source_repo,
                'criteria': {
                'type_ids': ['distribution']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_5_copy_erratum(self):

        source_repo = self.source_repo.id
        response = self.dest_repo2.copy(
            self.pulp,
            data={
                'source_repo_id': source_repo,
                'criteria': {
                'type_ids': ['erratum']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)

    def test_6_copy_srpm(self):

        source_repo = self.source_repo.id
        response = self.dest_repo2.copy(
            self.pulp,
            data={
                'source_repo_id': source_repo,
                'criteria': {
                'type_ids': ['srpm']
                },
            }
        )
        self.assertPulp(code=202)
        task = Task.from_response(response)
        task.wait(self.pulp)


    @classmethod
    def tearDownClass(cls):
        pass

