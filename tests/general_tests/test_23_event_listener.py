from pulp_auto.event_listener import EventListener
from pulp_auto.task import Task, TASK_RUNNING_STATE, TASK_FINISHED_STATE
from pulp_auto.repo import create_yum_repo
from tests.pulp_test import PulpTest, deleting
import json

try:
    from requestbin.bin import Bin
except ImportError as e:
        import unittest
        raise unittest.SkipTest(e)


class EventListenerTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        # set up a repo for the test cases
        super(EventListenerTest, cls).setUpClass()

        cls.repo_feed = 'https://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/'
        cls.repo, cls.importer, cls.distributor = create_yum_repo(cls.pulp, 'EventListenerRepo',
                                                        feed=cls.repo_feed)

    @classmethod
    def tearDownClass(cls):
        # tear down repo
        with deleting(cls.pulp, cls.repo, cls.importer, cls.distributor):
            pass
        super(EventListenerTest, cls).tearDownClass()

    def setUp(self):
        super(EventListenerTest, self).setUp()
        # set up a fresh service bin for each test in this class
        self.bin = Bin.create()
        # instantiate default http listener
        el = EventListener.http(self.bin.url)
        response = el.create(self.pulp)
        self.assertPulpOK()
        self.el = EventListener.from_response(response)

    def tearDown(self):
        # clean up the EventListener
        self.el.delete(self.pulp)
        self.assertPulpOK()
        super(EventListenerTest, self).tearDown()

    def test_01_cud(self):
        # get listener
        assert EventListener.get(self.pulp, self.el.id) == self.el, 'failed fetching %s' % self.el
        # list listeners
        assert self.el in EventListener.list(self.pulp), 'failed listing %s' % self.el
        # assert updating works
        self.el.update(self.pulp, {'event_types': ['repo.sync.finish', 'repo.sync.start']})
        self.assertPulpOK()
        self.el.reload(self.pulp)
        assert sorted(self.el.data['event_types']) == \
                sorted(['repo.sync.finish', 'repo.sync.start']), 'update failed: %s' % self.el

    def test_02_repo_sync_start(self):
        self.el.update(self.pulp, {'event_types': ['repo.sync.start']})
        self.assertPulpOK()
        self.el.reload(self.pulp)
        report = self.repo.sync(self.pulp)
        # wait till the sync is done
        Task.wait_for_report(self.pulp, report)
        # keep track of all the spawned tasks
        tasks = Task.from_report(self.pulp, report)
        assert tasks, 'no tasks induced'
        # fetch the request as POSTed by pulp event listener to the bin (http://requestb.in/<bin_id>)
        self.bin.reload()
        assert self.bin.request_count == 1, 'invalid event listener POST count (%s)' \
                                                % self.bin.request_count
        el_request = self.bin.requests[0]
        assert el_request.method == 'POST', 'invalid request method: %s' % el_request.method
        # assert the bin was POSTed no later any task finished
        tasks_finished_before_request = [task.id for task in tasks if el_request.time > task.finish_time]
        assert tasks_finished_before_request == [], 'tasks %s finished before request at: %s' % \
                (tasks_finished_before_request, el_request.time)
        # FIXME: not yet specified in docs: assert the bin was not POSTed before any task has started
        # tasks_started_after_request = [task.id for task in tasks if el_request.time < task.start_time]
        # assert tasks_started_after_request == [], 'tasks %s started after request at: %s' % \
        #        (tasks_started_after_request, el_request.time)

        # assert there's a task POSTed to the bin with the same ID pulp reported with sync
        # request.body contains original POSTed task-report-data --- create a Task object from it
        el_task = Task.from_call_report_data(json.loads(el_request.body))
        assert el_task.state == TASK_RUNNING_STATE, 'invalid task state: %s' % el_task.state
        el_task.reload(self.pulp)
        # assert the task is indeed in the tasks list spawned by pulp to perform repo sync
        assert el_task.id in [task.id for task in tasks], 'invalid task id posted: %s' % el_task.id
        assert sorted([u'pulp:repository:EventListenerRepo', u'pulp:action:sync']) == sorted(el_task.data['tags']), \
                'invalid task tags: %s' % el_task.data['tags']

    def test_03_repo_sync_finish(self):
        self.el.update(self.pulp, {'event_types': ['repo.sync.finish']})
        self.assertPulpOK()
        self.el.reload(self.pulp)
        report = self.repo.sync(self.pulp)
        # wait till the sync is done
        Task.wait_for_report(self.pulp, report)
        # fetch the tasks sync-call has spawned
        tasks = Task.from_report(self.pulp, report)
        assert tasks, 'no tasks induced'
        # check the requestsb.in got notified
        self.bin.reload()
        assert self.bin.request_count == 1, 'invalid event listener requests count: %s' % \
                                                self.bin.request_count
        el_request = self.bin.requests[0]
        assert el_request.method == 'POST', 'invalid request method: %s' % el_request.method
        # assert the bin was posted no sooner than all tasks have finished
        tasks_finished_after_request = [task.id for task in tasks if el_request.time < task.finish_time]
        assert tasks_finished_after_request, 'tasks %s finished after request at: %s' % \
                (tasks_finished_after_request, el_request.time)
        # the request body contains a task
        el_task = Task.from_call_report_data(json.loads(el_request.body))
        assert el_task.state == TASK_FINISHED_STATE, 'invalid task state: %s' % el_task.state
        el_task.reload(self.pulp)
        # assert proper task was posted
        assert el_task.id in [task.id for task in tasks], 'invalid task id posted: %s' % el_task.id
        assert sorted([u'pulp:repository:EventListenerRepo', u'pulp:action:sync']) == sorted(el_task.data['tags']), \
                'invalid task tags: %s' % el_task.data['tags']

    def test_04_repo_publish_start(self):
        self.el.update(self.pulp, {'event_types': ['repo.publish.start']})
        self.assertPulpOK()
        self.el.reload(self.pulp)
        report = self.repo.publish(self.pulp, self.distributor.id)
        # wait till report-induced tasks finish
        Task.wait_for_report(self.pulp, report)
        # fetch the tasks spawned for report; only
        sync_tasks = [task for task in Task.from_report(self.pulp, report) \
                if u'pulp:action:sync' in task.data['tags']]
        publish_tasks = [task for task in Task.from_report(self.pulp, report) \
                if u'pulp:action:publish' in task.data['tags']]
        assert publish_tasks, 'no publish tasks induced'
        self.bin.reload()
        assert self.bin.request_count == 1, 'invalid event listener requests count: %s' % \
                self.bin.request_count
        el_request = self.bin.requests[0]
        assert el_request.method == 'POST', 'invalid request method: %s' % el_request.method
        # assert the event was not triggered after any publish task finished
        publish_tasks_finished_before_request = [task.id for task in publish_tasks \
                if el_request.time > task.finish_time]
        assert publish_tasks_finished_before_request == [], '%s publish tasks finished before request at: %s' % \
                (publish_tasks_finished_before_request, el_request.time)
        # assert the event was not triggered before all sync tasks finished
        sync_tasks_finished_after_request = [task.id for task in sync_tasks \
                if el_request.time < sync_task.finish_time]
        assert sync_tasks_finished_after_request == [], '%s sync tasks finished after request at: %s' % \
                (sync_tasks_finished_after_request, el_request.time)
        # the request body contains a task
        el_task = Task.from_call_report_data(json.loads(el_request.body))
        assert el_task.state == TASK_RUNNING_STATE, 'invalid task state: %s' % el_task.state
        el_task.reload(self.pulp)
        # assert proper task was posted
        assert el_task.id in [task.id for task in publish_tasks], 'invalid task id posted: %s' % el_task.id
        assert sorted([u'pulp:repository:EventListenerRepo', u'pulp:action:publish']) == sorted(el_task.data['tags']), \
                'invalid task tags: %s' % el_task.data['tags']

    def test_05_repo_publish_finish(self):
        self.el.update(self.pulp, {'event_types': ['repo.publish.finish']})
        self.assertPulpOK()
        self.el.reload(self.pulp)
        report = self.repo.publish(self.pulp, self.distributor.id)
        # wait till publish-induced tasks finish
        Task.wait_for_report(self.pulp, report)
        # fetch the tasks spawned for the publish to perform
        tasks = [task for task in Task.from_report(self.pulp, report) \
                if u'pulp:action:publish' in task.data['tags']]
        assert tasks, 'no tasks induced'
        # assert bin status
        self.bin.reload()
        assert self.bin.request_count == 1, 'invalid event listener requests count: %s' % \
                self.bin.request_count
        el_request = self.bin.requests[0]
        # assert request method
        assert el_request.method == 'POST', 'invalid request method: %s' % el_request.method
        # assert the request was made after all tasks finished
        tasks_finished_after_request = [task.id for task in tasks if el_request.time < task.finish_time]
        assert tasks_finished_after_request == [], '%s finished after request at %s' % \
                (tasks_finished_after_request, el_request.time)
        # the request body contains a task
        el_task = Task.from_call_report_data(json.loads(el_request.body))
        assert el_task.state == TASK_FINISHED_STATE, 'invalid task state: %s' % el_task.state
        el_task.reload(self.pulp)
        # assert proper task was posted
        assert el_task.id in [task.id for task in tasks], 'invalid task id posted: %s' % el_task.id
        assert sorted([u'pulp:repository:EventListenerRepo', u'pulp:action:publish']) == sorted(el_task.data['tags']), \
                'invalid task tags: %s' % el_task.data['tags']

    def test_06_wildcard_events(self):
        # prepare event listener
        self.el.update(self.pulp, {'event_types': ['*']})
        self.assertPulpOK()
        self.el.reload(self.pulp)
        # trigger repo sync and publish; wait for related tasks to finish
        sync_report = self.repo.sync(self.pulp)
        Task.wait_for_report(self.pulp, sync_report)
        publish_report = self.repo.publish(self.pulp, self.distributor.id)
        Task.wait_for_report(self.pulp, publish_report)
        # fetch tasks data
        sync_tasks = Task.from_report(self.pulp, sync_report)
        publish_tasks = Task.from_report(self.pulp, publish_report)
        assert sync_tasks, 'no sync tasks induced'
        assert publish_tasks, 'no publish tasks induced'
        # assert bin status
        self.bin.reload()
        assert self.bin.request_count == 4, 'invalid event listener request count: %s' % \
                self.bin.request_count
        el_request_tasks = [Task.from_call_report_data(json.loads(request.body)) for request in self.bin.requests]
        # the POSTed tasks should look like this
        # - sync running task for repo.sync.start event
        # - sync finished task for repo.sync.finis  event
        # - publish running task for repo.publish.start event
        # - publish finished task for repo.publish.finish event
        el_sync_start_task, el_sync_finish_task, el_publish_start_task, el_publish_finish_task = el_request_tasks
        # sync part
        assert el_sync_start_task.state == TASK_RUNNING_STATE, 'invalid state: %s' % el_sync_start_task.state
        assert el_sync_start_task.id in [task.id for task in sync_tasks], 'invalid task posted: %s' % el_sync_start_task.id
        assert el_sync_finish_task.state == TASK_FINISHED_STATE, 'invalid state: %s' % el_sync_finish_task
        assert el_sync_finish_task.id in [task.id for task in sync_tasks], 'invalid task posted: %s' % el_sync_finish_task.id
        # start and finish are the same task but posted twice (with different state)
        assert el_sync_start_task.id == el_sync_finish_task.id, 'sync start and finish events refer to different tasks respectively'
        # publish part
        assert el_publish_start_task.state == TASK_RUNNING_STATE, 'invalid state: %s' % el_publish_start_task.state
        assert el_publish_start_task.id in [task.id for task in publish_tasks], 'invalid task posted: %s' % el_publish_start_task.id
        assert el_publish_finish_task.state == TASK_FINISHED_STATE, 'invalid state: %s' % el_publish_finish_task.state
        assert el_publish_finish_task.id in [task.id for task in publish_tasks], 'invalid task posted: %' % el_publish_finish_task.id
        # start and finish are the same task but posted twice (with different state)
        assert el_publish_start_task.id == el_publish_finish_task.id, 'publish start and finish events refer to different tasks respectively'
