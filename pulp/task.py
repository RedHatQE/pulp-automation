import item, time, hasdata

class AbstractTask(object):
    state = None
    active_states = []
    end_states = []

    def update(self, pulp):
        '''an abstract update does nothing'''
        pass

    def wait(self, pulp):
        '''wait while both of these conditions hold:
             - self.state in self.active_states
             - self.state not in self.end_states
        '''
        self.update(pulp)
        while self.state not in self.end_states and self.state in self.active_states:
            time.sleep(1)
            self.update(pulp)



class TaskDetails(hasdata.HasData):
    relevant_data_keys = [
        "response",
        "reasons",
        "state",
        "task_id",
        "task_group_id",
        "schedule_id",
        "progress",
        "result",
        "exception",
        "traceback",
        "start_time",
        "finish_time",
        "tags"
    ]
    required_data_keys = ['task_id', 'state']
    active_states = ['running', 'waiting']
    end_states = ['finished']

    @property
    def state(self):
        return self.data['state']



class Task(item.Item, TaskDetails, AbstractTask):
    '''an item-view task'''
    path = '/tasks/'



class GroupTask(item.GroupItem, TaskDetails, AbstractTask):
    '''task view from a task_group'''
    path = '/task_groups/'
    required_data_keys = TaskDetails.required_data_keys + ['task_group_id']

    @property
    def group_id(self):
        '''map to different field name'''
        return self.data['task_group_id']

    @group_id.setter
    def group_id(self, other):
        '''map to different field name'''
        return self.data['task_group_id']


TASK_DATA_EXAMPLE = {
    "_href": "/pulp/api/v2/tasks/7744e2df-39b9-46f0-bb10-feffa2f7014b/",
    "response": "postponed",
    "reasons": [{"resource_type": "repository", "resource_id": "test-repo", "operation": "update"}],
    "state": "running",
    "task_id": "7744e2df-39b9-46f0-bb10-feffa2f7014b",
    "task_group_id": None,
    "schedule_id": None,
    "progress": {},
    "result": None,
    "exception": None,
    "traceback": None,
    "start_time": "2012-05-13T23:00:02Z",
    "finish_time": None,
    "tags": ["pulp:repository:test-repo"],
}
    
