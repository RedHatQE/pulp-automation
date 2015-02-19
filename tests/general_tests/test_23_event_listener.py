from pulp_auto.event_listener import EventListener
from pulp_auto.task import Task
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
        # fetch the request as POSTed by pulp event listener to the bin (http://requestb.in/<bin_id>)
        self.bin.reload()
        assert self.bin.request_count == 1, 'invalid event listener POST count (%s)' \
                                                % self.bin.request_count
        el_request = self.bin.requests[0]
        # assert the bin was POSTed no later any task finished
        assert all(el_request.time < task.finish_time for task in tasks), \
                '%s finished before %s' % \
                ([task for task in tasks if task.finish_time >= el_request.time], task.finish_time)
        # assert there's a task POSTed to the bin with the same ID pulp reported with sync
        # request.body contains original POSTed task-report-data --- create a Task object from it
        el_task = Task.from_call_report_data(json.loads(el_request.body))
        el_task.reload(self.pulp)
        # assert the task is indeed in the tasks list spawned by pulp to perform repo sync
        assert el_task.id in [task.id for task in tasks], 'invalid task id posted: %s' % el_task.id
