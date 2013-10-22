from pulp.consumer import (Consumer, Binding)
from pulp.repo import create_yum_repo
from pulp.task import Task
from pulp_test import PulpTest


class TestConsumer(PulpTest):
    @classmethod
    def setUpClass(cls):
        super(TestConsumer, cls).setUpClass()
        cls.feed = 'http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'
        cls.repo, cls.importer, cls.distributor = create_yum_repo(
            cls.pulp,
            cls.__name__ + "_repo",
            cls.feed,
            '/' + cls.__name__ + '_repo/zoo/'
        )
        cls.consumer = Consumer({'id': cls.__name__ + '_consumer'})
        cls.consumer.create(cls.pulp)
        cls.binding_data = {'repo_id': cls.repo.id, 'distributor_id': cls.distributor.id}

    @classmethod
    def tearDownClass(cls):
        with cls.pulp.asserting(True):
            Task.wait_for_response(cls.pulp, cls.repo.delete(cls.pulp))
            cls.consumer.delete(cls.pulp)


    def test_01_update_consumer(self):
        self.consumer |= {'display_name': "A %s consumer" % type(self).__name__}
        with self.pulp.asserting(True):
            self.consumer.update(self.pulp)
            self.assertEqual(Consumer.get(self.pulp, self.consumer.id), self.consumer)
            
    def test_02_bind_distributor(self):
        with self.pulp.asserting(True):
            Task.wait_for_response(self.pulp, self.consumer.bind_distributor(self.pulp, self.binding_data))

    def test_03_get_repo_bindings(self):
        with self.pulp.asserting(True):
            bindings = self.consumer.get_repo_bindings(self.pulp, self.repo.id)
        binding = Binding(data={
            'repo_id': self.repo.id,
            'consumer_id': self.consumer.id,
            'distributor_id': self.distributor.id,
            'id': '123'
        })
        self.assertIn(binding, bindings)

    def test_04_list_bindings(self):
        with self.pulp.asserting(True):
            bindings = self.consumer.list_bindings(self.pulp)
        binding = Binding(data={
            'repo_id': self.repo.id,
            'consumer_id': self.consumer.id,
            'distributor_id': self.distributor.id,
            'id': '123'
        })
        self.assertIn(binding, bindings)

    def test_05_unbind_distributor(self):
        with self.pulp.asserting(True):
            Task.wait_for_response(self.pulp, self.consumer.unbind_distributor(self.pulp, self.repo.id, self.distributor.id))
