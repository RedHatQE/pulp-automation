import logging, profile
from pulp.namespace import load_ns
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

def unit_method(method):
    '''maps a method on all the units;
    *args -> units, options, unit_type; **kvs -> PROFILE;
    return PROFILE
    '''
    def wrapped_method(self, *args, **kvs):
        units = load_ns(args[0])
        options = load_ns(args[-1])
        # if there is no PROFILE in kvs, use a PROFILE copy from this module
        PROFILE = kvs.pop('PROFILE', profile.PROFILE.copy())
        type(self).augment_profile(units, PROFILE)
        # map the method on all the units
        PROFILE.num_changes = len(
            map(
                lambda unit: \
                    method(
                            self,
                            type(self).unit_type_map[unit.type_id],
                            unit,
                            PROFILE
                    ),
                units
            )
        )
        return PROFILE 
    wrapped_method.__name__ = method.__name__
    return wrapped_method


class Handler(object):
    '''generic Handler to execute via gofer-agent dispatch call'''
    unit_type_map = {}

    def __init__(self, *args, **kvs):
        # store the instantiation call
        self.args = args
        self.kvs = kvs

    def __repr__(self):
        return format_function_call(type(self).__name__, self.args, self.kvs)

    @classmethod
    def assert_units(cls, units):
        log.debug('asserting %s.unit_type_map: %s:' % (cls.__name__, cls.unit_type_map))
        for unit in units:
            log.debug('asserting: %s' % unit)
            assert 'type_id' in unit, 'Unit %r lacks type_id field' % unit
            assert unit.type_id in cls.unit_type_map, 'Unkown unit type: %r' % unit

    @classmethod
    def augment_profile(cls, units, PROFILE):
        # augment profile with requested unit types
        cls.assert_units(units)
        for unit_type in cls.unit_types(units):
            if unit_type not in PROFILE.details:
                PROFILE.details[unit_type] = []

    @staticmethod
    def unit_types(units):
        return set([unit.type_id for unit in units])

    @logged
    def profile(self, *args, **kvs):
        '''return the profile'''
        _PROFILE = kvs.pop('PROFILE', PROFILE.copy())
        _PROFILE.num_changes = 0
        return _PROFILE


class Admin(Handler):

    @logged
    def cancel(*args, **kvs):
        return {
            'succeeded': True
            # Dunno what to return here 
        }


