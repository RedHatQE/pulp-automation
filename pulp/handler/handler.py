import logging
log = logging.getLogger(__name__)

def format_function_call(fn_name, args, kvs):
    '''return a string representation of a fn_name(*args, **kvs) call'''
    rargs = map(lambda x: repr(x), args)
    rkvs = map(lambda x: "%s=%r" % (x[0], x[1]), kvs)
    return "%s(" % fn_name  + ", ".join(rargs + rkvs) + ")"

def logged(fn, log_method=log.info):
    '''decorate a method to log its calls and returned value'''
    def logged_wrapper(*args, **kvs):
        ret = None
        # method's first argument is always its 'self' object
        obj = args[0]
        try:
            ret = fn(*args, **kvs)
        finally:
            log_method(repr(obj) + "." + format_function_call(fn.__name__, args[1:], kvs) + " == " + repr(ret))
        return ret
    return logged_wrapper

class Handler(object):
    '''generic Handler to execute via gofer-agent dispatch call'''

    def __init__(self, *args, **kvs):
        # store the instantiation call
        self.args = args
        self.kvs = kvs

    def __repr__(self):
        return format_function_call(type(self).__name__, self.args, self.kvs)

class Admin(Handler):

    @logged
    def cancel(*args, **kvs):
        return {
            'succeeded': True
            # Dunno what to return here 
        }


