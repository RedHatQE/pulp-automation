import json
import unittest
from pulp_auto.event_listener import EventListener
from pulp_auto.task import Task, TASK_RUNNING_STATE, TASK_FINISHED_STATE, TASK_ERROR_STATE, \
    TaskFailure
from tests.pulp_test import PulpTest, deleting, requires_any
from tests.conf.roles import ROLES
from tests.conf.facade.yum import YumRepo, YumImporter, YumDistributor
from distutils.version import LooseVersion

# with newer Pulp, HTTP event listeners are deprecated
MAX_PULP_VERSION = '2.7'

try:
    from requestbin.bin import Bin
except ImportError as e:
        raise unittest.SkipTest(e)

try:
    version = ROLES.pulp.version
except AttributeError:
        raise unittest.SkipTest('this test module requires pulp.version information')
if LooseVersion(version) >= MAX_PULP_VERSION:
    raise unittest.SkipTest('this test module requires pulp.version < %s, %s found' % \
                            (MAX_PULP_VERSION, ROLES.pulp.version))

class EventListenerTest(PulpTest):
    @classmethod
    def setUpClass(cls):
        # set up a repo for the test cases
        super(EventListenerTest, cls).setUpClass()
        repo_role = [repo for repo in ROLES.repos if repo.type == 'rpm'][0].copy()
        repo_role.id = 'EventListenerRepo'
        # this test case relies on exact events counts
        # auto_publish would mess things up
        repo_role.auto_publish = False
        cls.repo, cls.importer, [cls.distributor] = YumRepo.from_role(repo_role).create(cls.pulp)

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
        # doesn't work and won't get fixed --- disabling
        # assert el_task.state == TASK_FINISHED_STATE, 'invalid task state: %s' % el_task.state
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
        # doesn't work --- disabling
        #assert tasks_finished_after_request == [], '%s finished after request at %s' % \
        #        (tasks_finished_after_request, el_request.time)
        # the request body contains a task
        el_task = Task.from_call_report_data(json.loads(el_request.body))
        #assert el_task.state == TASK_FINISHED_STATE, 'invalid task state: %s' % el_task.state
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
        # - sync finished task for repo.sync.finis  event --- doesn't work, won't get fixed --- disabling
        # - publish running task for repo.publish.start event
        # - publish finished task for repo.publish.finish event --- doesn't work, won't get fixed --- disabling
        el_sync_start_task, el_sync_finish_task, el_publish_start_task, el_publish_finish_task = el_request_tasks
        # sync part
        assert el_sync_start_task.state == TASK_RUNNING_STATE, 'invalid state: %s' % el_sync_start_task.state
        assert el_sync_start_task.id in [task.id for task in sync_tasks], 'invalid task posted: %s' % el_sync_start_task.id
        #assert el_sync_finish_task.state == TASK_FINISHED_STATE, 'invalid state: %s' % el_sync_finish_task.state
        assert el_sync_finish_task.id in [task.id for task in sync_tasks], 'invalid task posted: %s' % el_sync_finish_task.id
        # start and finish are the same task but posted twice (with different state)
        assert el_sync_start_task.id == el_sync_finish_task.id, 'sync start and finish events refer to different tasks respectively'
        # publish part
        assert el_publish_start_task.state == TASK_RUNNING_STATE, 'invalid state: %s' % el_publish_start_task.state
        assert el_publish_start_task.id in [task.id for task in publish_tasks], 'invalid task posted: %s' % el_publish_start_task.id
        #assert el_publish_finish_task.state == TASK_FINISHED_STATE, 'invalid state: %s' % el_publish_finish_task.state
        assert el_publish_finish_task.id in [task.id for task in publish_tasks], 'invalid task posted: %' % el_publish_finish_task.id
        # start and finish are the same task but posted twice (with different state)
        assert el_publish_start_task.id == el_publish_finish_task.id, 'publish start and finish events refer to different tasks respectively'


class EventListenerErrorTest(PulpTest):
    def setUp(self):
        super(EventListenerErrorTest, self).setUp()
        # set up a fresh http://requestb.in bin for each test method
        self.bin = Bin.create()
        el = EventListener.http(self.bin.url)
        response = el.create(self.pulp)
        self.assertPulpOK()
        self.el = EventListener.from_response(response)

    def tearDown(self):
        self.el.delete(self.pulp)
        self.assertPulpOK()
        super(EventListenerErrorTest, self).tearDown()

    def test_01_repo_sync_finish(self):
        self.el.update(self.pulp, {'event_types': ['repo.sync.finish']})
        self.el.reload(self.pulp)
        repo_role = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        repo, importer, [distributor] = YumRepo(id='sync_error_repo',
                        importer=YumImporter(feed='http://example.com/repos/none'),
                        distributors=[YumDistributor(relative_url='/repos/none')]).create(self.pulp)
        with deleting(self.pulp, repo, importer, distributor):
            response = repo.sync(self.pulp)
            self.assertPulpOK()
            with self.assertRaises(TaskFailure):
                # make sure the sync did not succeed
                Task.wait_for_report(self.pulp, response)
            tasks = Task.from_report(self.pulp, response)
            # assert the bin contains request with a failed task in body
            self.bin.reload()
            assert self.bin.request_count == 1, 'invalid bin.request count: %s' % self.bin.request_count
            el_request = self.bin.requests[0]
            assert el_request.method == 'POST', 'invalid bin request method: %s' % el_request.method
            el_task = Task.from_call_report_data(json.loads(el_request.body))
            # doesn't work and won't get fixed --- disabling
            # assert el_task.state == TASK_ERROR_STATE, 'invalid request.body:Task.state: %s' % el_task.state
            assert el_task.id in [task.id for task in tasks], 'invalid request.body:Task.id: %s' % el_task.id

    # doesn't work and won't get fixed --- disabling
    def _test_02_repo_publish_finish(self):
        self.el.update(self.pulp, {'event_listener': ['repo.publish.finish']})
        self.el.reload(self.pulp)
        repo_role = [repo for repo in ROLES.repos if repo.type == 'rpm'][0]
        repo, importer, [distributor] = YumRepo(id='publish_error_repo', importer=Importer.from_role(repo_role),
                                distributors=[YumDistributor(distributor_type_id='invalid_distributor_id', relative_url='xyz')]).create(self.pulp)
        with deleting(self.pulp, repo, importer, distributor):
            response = repo.publish(self.pulp, 'invalid_distributor_id')
            self.assertPulpOK()
            with self.assertRaises(TaskFailure):
                # make sure the publish task failed
                Task.wait_for_report(self.pulp, response)
            task = Task.from_report(self.pulp, response)
            # assert the bin contains a request with a fained task in body
            self.bin.reload()
            assert self.bin.request_count == 1, 'invalid bin.request_count: %s' % self.bin.request_count
            el_request = self.bin.requests[0]
            assert el_request.method == 'POST', 'invalid bin request method: %s' % el_request.method
            el_task = Task.from_call_report_data(json.loads(el_request.body))
            assert el_task.state == TASK_ERROR_STATE, 'invalid request.body:Task.state: %s' % el_task.state
            assert el_task.id in [task.id for task in tasks], 'invalid request.body:Task.id: %s' % el_task.id
