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
            consumer.update(self.pulp)
            self.assertEqual(Consumer.get(self.pulp, consumer.id), consumer)
    
    ### binding
    
    @agent_test(catching=True)
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
            Task.wait_for_response(self.pulp, self.consumer.unbind_distributor(self.pulp, self.repo.id, self.distributor.id))
            
    ### consumer info
    
    def test_07_get_consumer_info(self):
        consumer = Consumer.get(self.pulp, self.consumer.id)
        self.assertEqual(consumer.id, self.consumer.id)
    
    def test_08_get_list_consumers(self):
        self.assertIn(Consumer.get(self.pulp, self.consumer.id), Consumer.list(self.pulp))
    
    #def test_09_search_consumers(self):
    
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
            events = self.consumer.get_history(self.pulp, {'limit': '5'})
        self.assertEqual(len(events), 5, "limit fail") 
    
    def test_13_event_history_filter_sort(self):
        with self.pulp.asserting(True):
            events = self.consumer.get_history(self.pulp, {'sort': 'ascending'})
        self.assertEqual(events, sorted(events, key = lambda event: event.data['timestamp']))
        
    def test_14_event_history_filter_all(self):
        with self.pulp.asserting(True):
            events = self.consumer.get_history(self.pulp, {'event_type': 'consumer_registered', 'limit': '5', 'sort': 'descending'})
        assert [event for event in events if event.data['type'] == "consumer_registered"], "consumer_registered event not found"
        assert [event for event in events if event.data['type'] != "repo_bound"], "repo_bound event found"
        self.assertEqual(len(events), 5, "limit fail")
        self.assertEqual(events, sorted(events, key = lambda event: event.data['timestamp'], reverse=True))
    
    ### profiles
    
    #def test_15_create_profile(self):
    
    #def test_16_replace_profile(self):
    
    #def test_17_list_profiles(self):
    
    #def test_18_get_profile(self):
    
    ### content
    
    #def test_19_install_content(self):
    
    #def test_20_update_content(self):
    
    #def test_21_unistall_content(self):
    
    ### schedules
        
    ### applicability
