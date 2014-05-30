from hashlib import sha256
from M2Crypto import RSA, BIO
from pulp import StaticRequest
import handler
import logging
log = logging.getLogger(__name__)


class AuthenticationError(AssertionError):
    '''to be risen when authentication fails'''


class Authenticator(object):
    '''perform auth of some data'''
    def __init__(self, signing_key=None, verifying_key=None):
        '''
        signing key: private key of an endpoint to sign the content with
        verifying_key: public key of an(other) endpoint to verify data and its signature with
        '''
        self.signing_key = signing_key
        self.verifying_key = verifying_key

    def __repr__(self):
        return type(self).__name__ + '(signing_key=%r, verifying_key=%s)' % (self.signing_key, self.verifying_key)


    @staticmethod
    def digest(data):
        '''
        return sha256 digest of data
        '''
        sha256_hash = sha256()
        sha256_hash.update(data)
        return sha256_hash.hexdigest()

    @handler.logged(log.debug)
    def sign(self, data):
        '''
        sign the data with self.signing_key
        returns the signed data digest
        '''
        if not self.signing_key:
            return None
        return self.signing_key.sign(Authenticator.digest(data))

    @handler.logged(log.debug)
    def verify(self, data, signature):
        '''
        verify data against signature using self.verifying_key
        raises AuthenticationError should verification fail
        '''
        if not self.verifying_key:
            return
        try:
            result = self.verifying_key.verify(self.digest(data), signature)
        except RSA.RSAError as e:
            # rethrow as assertion-authentication failure
            import traceback
            t = traceback.format_exc(e)
            raise AuthenticationError(t)
        if not result:
            raise AuthenticationError("Verification failed for: %s, %s, %s" % (self, data, signature))



    

