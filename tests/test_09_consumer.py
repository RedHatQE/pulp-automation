import unittest
from pulp_auto.consumer.consumer_class import (Consumer, Binding, Event) 
from pulp_auto.task import Task 
from pulp_test import (ConsumerAgentPulpTest, agent_test)


class TestConsumer(ConsumerAgentPulpTest):

    def test_00_none(self):
        pass

    def test_01_update_consumer(self):
        # update causes private key loss; do not change self.consumer 
        consumer = self.consumer | {'display_name': "A %s consumer" % type(self).__name__}
        with self.pulp.asserting(True):
            consumer.delta_update(self.pulp)
            self.assertEqual(Consumer.get(self.pulp, consumer.id), consumer)
    
    ### binding
    
    @agent_test(catching=True)
    def test_02_bind_distributor(self):
        with self.pulp.asserting(True):
            response = self.consumer.bind_distributor(self.pulp, self.repo.id, self.distributor.id)
            self.assertPulp(code=202)
            Task.wait_for_report(self.pulp, response)


    @agent_test(catching=True)
    def test_02_bind_non_existant_distributor(self):
        self.consumer.bind_distributor(self.pulp, self.repo.id, 'some_dist')
        self.assertPulp(code=404)


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


    def test_03_get_nonexistant_repo_bindings_bz1094264(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1094264
        with self.assertRaises(AssertionError):
            self.consumer.get_repo_bindings(self.pulp, 'some_repo')
        self.assertPulp(code=404)
        
    def test_04_get_single_binding(self):
        with self.pulp.asserting(True):
            single_binding = self.consumer.get_single_binding(self.pulp, self.repo.id, self.distributor.id)
        binding = Binding(data={
            'repo_id': self.repo.id,
            'consumer_id': self.consumer.id,
            'distributor_id': self.distributor.id,
            'id': '123'
        })
        self.assertEqual(binding, single_binding)

    def test_04_get_nonexistant_binding(self):
        with self.assertRaises(AssertionError):
            self.consumer.get_single_binding(self.pulp, self.repo.id, 'some_dist')
            self.assertPulp(code=404)


    def test_05_list_bindings(self):
        with self.pulp.asserting(True):
            bindings = self.consumer.list_bindings(self.pulp)
        binding = Binding(data={
            'repo_id': self.repo.id,
            'consumer_id': self.consumer.id,
            'distributor_id': self.distributor.id,
            'id': '123'
        })
        self.assertIn(binding, bindings)

    @agent_test(catching=True)
    def test_06_unbind_distributor(self):
        with self.pulp.asserting(True):
            response = self.consumer.unbind_distributor(self.pulp, self.repo.id, self.distributor.id)
            self.assertPulp(code=202)
            Task.wait_for_report(self.pulp, response)

    @agent_test(catching=True)
    def test_06_unbind_non_existant_distributor(self):
        self.consumer.unbind_distributor(self.pulp, self.repo.id, 'some_dist')
        self.assertPulp(code=404)
            
    ### consumer info

    def test_07_get_consumer_info(self):
        consumer = Consumer.get(self.pulp, self.consumer.id)
        self.assertEqual(consumer.id, self.consumer.id)

    def test_07_get_nonesistant_consumer_info(self):
        with self.assertRaises(AssertionError):
            Consumer.get(self.pulp, 'some_consumer')
            self.assertPulp(code=404)

    def test_08_get_list_consumers(self):
        self.assertIn(Consumer.get(self.pulp, self.consumer.id), Consumer.list(self.pulp))
    
    def test_09_search_consumer(self):
        #perfom searh of the consumer by its id
        #check that the filter works properly and as a result gave right consumer id
        consumer = Consumer.search(self.pulp, data={"criteria": {"sort": None, "fields": None, "limit": None, "filters": {"id": self.consumer.id}, "skip": None}})
        self.assertIn(Consumer({"id": self.consumer.id}, ['id'], ['id']), consumer)
        #check that in the search result there is only one and unique consumer with such id
        self.assertTrue(len(consumer) == 1)
    
    ### history
    
    def test_10_event_history(self):
        events = self.consumer.get_history(self.pulp)
        self.assertPulp(code=200)
        
    def test_11_event_history_filter_type(self):
        with self.pulp.asserting(True):
            events = self.consumer.get_history(self.pulp, {'event_type': 'consumer_registered'})
        assert [event for event in events if event.data['type'] == "consumer_registered"], "consumer_registered event not found"
        assert [event for event in events if event.data['type'] != "consumer_unregistered"], "consumer_unregistered event found"
        assert [event for event in events if event.data['type'] != "repo_bound"], "repo_bound event found"
        
    def test_12_event_history_filter_limit(self):
        with self.pulp.asserting(True):
            events = self.consumer.get_history(self.pulp, {'limit': '2'})
        self.assertEqual(len(events), 2, "limit fail")
    
    def test_13_event_history_filter_sort(self):
        with self.pulp.asserting(True):
            events = self.consumer.get_history(self.pulp, {'sort': 'ascending'})
        self.assertEqual(events, sorted(events, key = lambda event: event.data['timestamp']))
        
    def test_14_event_history_filter_all(self):
        with self.pulp.asserting(True):
            events = self.consumer.get_history(self.pulp, {'event_type': 'consumer_registered', 'limit': '2', 'sort': 'descending'})
        assert [event for event in events if event.data['type'] == "consumer_registered"], "consumer_registered event not found"
        assert [event for event in events if event.data['type'] != "repo_bound"], "repo_bound event found"
        self.assertEqual(len(events), 2, "limit fail")
        self.assertEqual(events, sorted(events, key = lambda event: event.data['timestamp'], reverse=True))
    
    ### profiles
    
    #def test_15_create_profile(self):
    
    #def test_16_replace_profile(self):
    
    #def test_17_list_profiles(self):
    
    #def test_18_get_profile(self):
        
    ### applicability
