import contextlib, logging


class Agent(object):
    '''consumer agent object. Handles envelopes, routing, secrets... And the remote calls'''

    def __init__(self, module, catching=False):
        self.module = module
        self._catching = catching
        self.log = logging.getLogger(__name__ + "." + str(self))
        self.log.addHandler(logging.StreamHandler())

    def __repr__(self):
        return type(self).__name__ + "(%(module)r, catching=%(_catching)r)" % self.__dict__

    @staticmethod
    def strip_request(request):
        '''strip the envelope from the request; return envelope and the request'''
        return { k: request[k] for k in request.keys() if k != 'request'}, request['request']

    @staticmethod
    def make_response(envelope, response):
        ret = envelope.copy()
        ret['result'] = {
            'retval': response
        }
        return ret

    @staticmethod
    def make_exception(envelope, exception):
        ret = envelope.copy()
        ret['result'] = {
            'exval': exception
        }
        return ret

    @staticmethod
    def invert_envelope(envelope):
        ''''return envelope copy suitable for request-to-response processing'''
        envelope = envelope.copy()
        # strip non-required keys
        for key in ['routing', 'replyto']:
            envelope.pop(key, None)
        return envelope

    @staticmethod
    def request_to_call(module, request):
        # instnatiate required class based on request.classname
        # call required method
        obj = getattr(module, request['classname'])()
        return lambda: make_response(envelope, getattr(obj, request['method'])(request['args'], request['kws']))

    def __call__(self, qpid_handle):
        '''dispatch a single RMI request--response'''
        # get the request
        envelope, request = self.strip_request(qpid_handle.message)
        self.log.debug("dispatching: %r; %r" % (envelope, request))
        # dispatch
        if self._catching:
            try:
                response = self.make_response(envelope, self.request_to_call(self.module, request)())
            except Exception as e:
                import traceback
                response = self.make_exception(envelope, {'Traceback': traceback.format_exc(e)})
        else:
            response = self.make_response(envelope, self.request_to_call(self.module, request)())

        # send the response
        qpid_handle.message = response 
        
    @contextlib.contextmanager
    def catching(self, value=True):
        '''propagate exception as an exception response message to the other end'''
        old_value = self._catching
        self._catching = value
        try:
            yield
        finally:
            self._catching = old_value

