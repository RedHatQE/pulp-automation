import contextlib, logging


class Agent(object):
    '''consumer agent object. Handles envelopes, routing, secrets... And the remote calls'''

    def __init__(self, module, catching=False):
        self.module = module
        self._catching = catching
        self.log = logging.getLogger(__name__ + "." + type(self).__name__)

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
    def make_status(envelope, status):
        ret = envelope.copy()
        ret['status'] = status
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
        ''' return a lambda that performs instnatiating required class
        and calling required method upon execution'''
        cargs=[]
        ckvs={}
        # assert sanity of the fields is mainained
        if 'cntr' in request and request['cntr'] is not None:
            assert isinstance(request['cntr'], list)
            assert len(request['cntr']) == 2
            cargs = cntr[0]
            ckvs = cntr[1]
            assert isinstance(cargs, list)
            assert isinstance(ckvs, dict)
        assert 'args' in request and isinstance(request['args'], list)
        assert 'kws' in request and isinstance(request['kws'], dict)
            
        return lambda: \
            getattr(
                    # instantiate required object
                    getattr(
                        module,
                        request['classname']
                    )(
                        *cargs,
                        **ckvs
                    ),
                    # access required method
                    request['method']
            )(
                # call required object method with requested signature
                *request['args'],
                **request['kws']
            )
        

    def __call__(self, qpid_handle):
        '''dispatch a single RMI request--response'''
        # get the request
        envelope, request = self.strip_request(qpid_handle.message)
        self.log.debug("dispatching: %r; %r" % (envelope, request))
        # invert envelope
        envelope = self.invert_envelope(envelope)
        # accept the message
        qpid_handle.message = self.make_status(envelope, 'accepted')
        # dispatch
        if self._catching:
            try:
                response = self.request_to_call(self.module, request)()
            except Exception as e:
                # when in cathcing mode, propagate all exceptions to the remote end
                import traceback
                t = traceback.format_exc(e)
                self.log.warning("propagating failure: %s" % t)
                qpid_handle.message = self.make_exception(envelope, {'Traceback': t})
                return
        else:
                response = self.request_to_call(self.module, request)()

        # send the response
        qpid_handle.message = self.make_response(envelope, response)
        
    @contextlib.contextmanager
    def catching(self, value=True):
        '''propagate exception as an exception response message to the other end'''
        old_value = self._catching
        self._catching = value
        try:
            yield
        finally:
            self._catching = old_value

