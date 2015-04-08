import os
from pulp_auto import path_join
from pulp_auto.item import Item
from pulp_auto.pulp import Request, ResponseLike
from pulp_auto.handler import logged
from contextlib import contextmanager

RPMTAG_NOSOURCE = 1051

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
        # data returned from the 201 response lacks original metadata
        upload |= data
        return upload

    def chunk(self, pulp, data):
        '''upload a chunk of data'''
        with pulp.asserting(True):
            pulp.send(self.request('PUT', path=str(self.offset), data=data,
                headers={'content-type': 'application/octet-stream'}))
        # augment self.offset accordingly
        self.reset(self.offset + len(data))

    def file(self, pulp, fd, chunksize=524288):
        '''stream from given fd'''
        while True:
            chunk = fd.read(chunksize)
            if not chunk:
                break
            self.chunk(pulp, chunk)

    def import_to(self, pulp, repo):
        '''import self into repo'''
        return pulp.send(repo.request('POST', path='actions/import_upload/', data=self.data))

def file_checksum(fd, chunksize=65536, checksum_type='sha256'):
    '''get file hashlib checksum'''
    import hashlib
    checksum = hashlib.new(checksum_type)
    fd.seek(0)
    while True:
        data = fd.read(chunksize)
        if not data:
            break
        checksum.update(data)
    return checksum.hexdigest()

def file_size(fd):
    '''
    get filesize with seeking to the end of file
    '''
    fd.seek(0,2)
    return fd.tell()

def rpm_metadata(fd):
    '''
    get rpm metadata.
    Usage: Upload.create(pulp, data=rpm_metadata(fd), ...)
    '''
    # almost a copy of pulp_rpm/pulp_rpm/src/pulp_rpm/extension/admin/upload/package.py

    import rpm
    transaction_set = rpm.TransactionSet()
    transaction_set.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
    # get headers
    headers = transaction_set.hdrFromFdno(fd)
    # compute checksum
    checksum = file_checksum(fd)

    # -- Unit Key
    # Name, Version, Release, Epoch
    unit_key = dict(checksumtype='sha256', checksum=file_checksum(fd, checksum_type='sha256'),
        name=headers.name, version=headers.version, release=headers.release, epoch=headers.epoch)

    # Epoch munging
    key = 'epoch'
    if unit_key[key] is None:
        unit_key[key] = str(0)
    else:
        unit_key[key] = str(unit_key[key])

    # Arch
    key = 'arch'
    unit_type_id = 'rpm'
    if headers.sourcepackage:
        unit_type_id = 'srpm'
        if RPMTAG_NOSOURCE in headers:
            unit_key[key] = 'nosrc'
        else:
            unit_key[key] = 'src'
    else:
        unit_key[key] = headers.arch


    # -- Metadata
    fd_basename = os.path.basename(fd.name)
    unit_metadata = dict(relativepath=fd_basename, filename=fd_basename, buildhost=headers.buildhost,
        license=headers.license, vendor=headers.vendor, description=headers.description)


    return dict(override_config=dict(), unit_type_id=unit_type_id, unit_key=unit_key,
        unit_metadata=unit_metadata)

def iso_metadata(fd):
    '''
    get iso metadata.
    Usage: Upload.create(pulp, data=iso_metadata(fd), ...)
    '''
    checksum = file_checksum(fd)
    size = file_size(fd)

    unit_key = dict(checksumtype='sha256', checksum=checksum, name=fd.name, size=size)

    return dict(unit_key=unit_key)
