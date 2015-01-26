from pulp_auto import path_join
from pulp_auto.item import Item
from pulp_auto.pulp import Request, ResponseLike
from pulp_auto.handler import logged
from contextlib import contextmanager


class Upload(Item):
    path = '/content/uploads/'
    required_data_keys = ['upload_id']
    relevant_data_keys = ['upload_id', 'unit_type_id', 'unit_key', 'unit_metadata']

    def reset(self, value=0):
        '''reset self.offset to given value'''
        self.offset = value

    def __init__(self, data={}):
        super(Upload, self).__init__(data=data)
        self.reset()

    @property
    def id(self):
        return self.data['upload_id']

    @id.setter
    def id(self, value):
        self.data['upload_id'] = value


    # from_response inherited from Item
    # GET method not supported see https://bugzilla.redhat.com/show_bug.cgi?id=1058771
    @classmethod
    def get(cls, pulp, id):
        '''no GET method allowed (405)'''
        assert pulp.send(Request('GET', path_join(cls.path, id))) == ResponseLike(405)
        raise TypeError('Uploads do not support GET method')

    @classmethod
    def list(cls, pulp):
        '''
        Uploads have custom list API
        @return: list of upload ids
        '''
        with pulp.asserting(True):
            data = pulp.send(Request('GET', cls.path)).json()
        assert 'upload_ids' in data, "invalid data received: %s" % data
        return data['upload_ids']


    @classmethod
    def create(cls, pulp, data={}):
        '''create an upload in pulp; upload.data is based on pulp response'''
        upload = cls.from_response(pulp.send(Request('POST', cls.path, data=data)))
        return upload

    def chunk(self, pulp, data):
        '''upload a chunk of data'''
        with pulp.asserting(True):
            pulp.send(self.request('PUT', path=str(self.offset), data=data))
        # augment self.offset accordingly
        self.reset(self.offset + len(data))

    def file(pulp, fd, chunksize=524288):
        '''stream from given fd'''
        while True:
            chunk = fd.read(chunksize)
            if not chunk:
                break
            self.chunk(pulp, chunk)

