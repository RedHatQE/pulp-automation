from tests.pulp_test import PulpTest
from pulp_auto.upload import Upload

class UploadCudTest(PulpTest):
    def testcase_01_create_delete_upload(self):
        '''test creating uploads works'''
        upload = Upload.create(self.pulp)
        # assert what was created is what is kept locally
        ids = Upload.list(self.pulp)
        assert upload.id in ids, 'could not find id %s on server (%s)' % (upload.id, ids)
        # assert GET doesn't work
        with self.assertRaises(TypeError):
            Upload.get(self.pulp, upload.id)

        # assert deleting works
        upload.delete(self.pulp)
        self.assertPulpOK()
        ids = Upload.list(self.pulp)
        assert upload.id not in ids, 'upload %s deleted but still on server (%s)' % (upload.id, ids)


