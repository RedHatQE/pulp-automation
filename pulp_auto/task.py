import item, time, hasdata
from item import (Item, GroupItem)
from pulp_auto.pulp import Request
from pulp_auto import strip_url

class TaskFailure(RuntimeError):
    def __init__(self, *args, **kvs):
        self.task = kvs.pop('task', None)
        super(TaskFailure, self).__init__(*args, **kvs)


class AbstractTask(object):
    state = None
    active_states = []
    end_states = []
    error_state = []

    def update(self, pulp):
        '''an abstract update does nothing'''
        pass

    def wait(self, pulp, timeout=60, frequency=0.5):
        '''wait while all of these conditions hold:
             - self.state in self.active_states
             - self.state not in self.end_states
             - timeout not elapsed yet
        '''
        delta = time.time() + timeout
        while time.time() <= delta:
            time.sleep(frequency)
            try:
                self.reload(pulp)
            except AssertionError as e:
                # task gone --- no need to wait anymore
                break
            if self.state in self.end_states:
                break
        else:
            raise TaskFailure('Timeout') 
        if self.state in 'error':
            raise TaskFailure('Task failed: %r' % self.data['error'], task=self)

class TaskDetails(hasdata.HasData):
    relevant_data_keys = [
        "error",
        "state",
        "task_id",
        "progress_report",
        "result",
        "exception",
        "traceback",
        "start_time",
        "finish_time",
        "tags"
    ]
    required_data_keys = ['task_id', 'state']
    active_states = ['running', 'waiting']
    end_states = ['finished', 'error', 'canceled', 'cancelled']

    @property
    def state(self):
        return self.data['state']

    @property
    def id(self):
        return self.data['task_id']

    @id.setter
    def id(self, other):
        self.data['task_id'] = other


class Task(TaskDetails, AbstractTask, Item):
    '''an item-view task'''
    path = '/tasks/'

    @classmethod
    def wait_for_response(cls, pulp, response):
        '''a shortcut for wait & from_response'''
        ret = cls.from_response(response)
        if isinstance(ret, list):
            # more than one task pending
            for task in ret:
                task.wait(pulp)
        else:
            ret.wait(pulp)

    @classmethod
    def wait_for_report(cls, pulp, response):
        # now every asyncronous call returns a call report object
        # call report has 'spawned_tasks' that contains list of tasks
        # meanwhile every tasks can have its own spawned tasks
        ret = cls.from_report(response)['spawned_tasks']
        if isinstance(ret, list):
            for task in ret:
                task_resp = pulp.send(Request('GET', strip_url(task['_href'])))
                Task.wait_for_response(pulp, task_resp)
                task_resp = pulp.send(Request('GET', strip_url(task['_href'])))
                if 'spawned_tasks' in Task.from_response(task_resp).data:
                    Task.wait_for_report(pulp, task_resp)


TASK_DATA_EXAMPLE = {
 "_href": "/pulp/api/v2/tasks/0fe4fcab-a040-11e1-a71c-00508d977dff/",
 "state": "running",
 "task_id": "0fe4fcab-a040-11e1-a71c-00508d977dff",
 "progress": {}, # contents depend on the operation
 "result": None,
 "start_time": "2012-05-17T16:48:00Z",
 "finish_time": None,
 "tags": [
   "pulp:repository:f16",
   "pulp:action:sync"
 ],
 "spawned_tasks": [{"href": "/pulp/api/v2/tasks/7744e2df-39b9-46f0-bb10-feffa2f7014b/",
                    "task_id": "7744e2df-39b9-46f0-bb10-feffa2f7014b" }],
 "error": None
}
