import logging, sys
from namespace import load_ns
log = logging.getLogger(__name__)

### FIXME: change internal representation of profile; atm delete content doesn't work

# a lump of custom profile data
# makes the fake-consumer a Fedora 19 system
PROFILE = load_ns({
    'reboot': {
        'scheduled': False,
        'details': {}
    },
    'details': {
        'rpm': {
            'details': [
                   {'vendor': 'Fedora Project', 'name': 'perl-Carp', 'epoch': 0, 'version': '1.26', 'release': '243.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'boost-program-options', 'epoch': 0, 'version': '1.53.0', 'release': '14.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'basesystem', 'epoch': 0, 'version': '10.0', 'release': '8.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'perl-PathTools', 'epoch': 0, 'version': '3.40', 'release': '3.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libibverbs', 'epoch': 0, 'version': '1.1.7', 'release': '3.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'tzdata', 'epoch': 0, 'version': '2013c', 'release': '1.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'perl', 'epoch': 4L, 'version': '5.16.3', 'release': '265.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'python-simplejson', 'epoch': 0, 'version': '3.2.0', 'release': '1.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libstdc++', 'epoch': 0, 'version': '4.8.1', 'release': '1.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'perl-Git', 'epoch': 0, 'version': '1.8.3.1', 'release': '1.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'xerces-c', 'epoch': 0, 'version': '3.1.1', 'release': '4.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libattr', 'epoch': 0, 'version': '2.4.46', 'release': '10.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'gpm-libs', 'epoch': 0, 'version': '1.20.6', 'release': '33.fc19', 'arch': 'x86_64'},
                   {'vendor': None, 'name': 'm2crypto', 'epoch': 0, 'version': '0.21.1.pulp', 'release': '8.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'zlib', 'epoch': 0, 'version': '1.2.7', 'release': '10.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'qpid-cpp-client', 'epoch': 0, 'version': '0.24', 'release': '3.fc19.1', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'python-rhsm', 'epoch': 0, 'version': '1.10.1', 'release': '1.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'chkconfig', 'epoch': 0, 'version': '1.3.60', 'release': '3.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'python-qpid', 'epoch': 0, 'version': '0.24', 'release': '1.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'python-oauth2', 'epoch': 0, 'version': '1.5.211', 'release': '4.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'libdb', 'epoch': 0, 'version': '5.3.21', 'release': '11.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'qpid-cpp-server', 'epoch': 0, 'version': '0.24', 'release': '3.fc19.1', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'boost-timer', 'epoch': 0, 'version': '1.53.0', 'release': '14.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libgpg-error', 'epoch': 0, 'version': '1.11', 'release': '1.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libxml2-python', 'epoch': 0, 'version': '2.9.1', 'release': '1.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'readline', 'epoch': 0, 'version': '6.2', 'release': '6.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'boost-iostreams', 'epoch': 0, 'version': '1.53.0', 'release': '14.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'lua', 'epoch': 0, 'version': '5.1.4', 'release': '12.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'boost-test', 'epoch': 0, 'version': '1.53.0', 'release': '14.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libffi', 'epoch': 0, 'version': '3.0.13', 'release': '4.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'boost-context', 'epoch': 0, 'version': '1.53.0', 'release': '14.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'tcp_wrappers-libs', 'epoch': 0, 'version': '7.6', 'release': '73.fc19', 'arch': 'x86_64'},
            ],
            'succeeded': True
        }
    }, 
    'succeeded': True,
    'num_changes': 0
})

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

def content_method(method):
    '''wrapper *args -> units, options; **kvs -> PROFILE'''
    def wrapped_method(self, *args, **kvs):
        units = Content.args_units(*args)
        options = Content.args_options(*args)
        # if there is no PROFILE in kvs, use a PROFILE copy from this module
        _PROFILE = kvs.pop('PROFILE', PROFILE.copy())
        return method(self, units, options, _PROFILE)
    wrapped_method.__name__ = method.__name__
    return wrapped_method

def requires_units(method):
    '''asserts required units are in PROFILE'''
    def wrapped_method(self, units, options, PROFILE):
        unit_keys = []
        for type_id in PROFILE.details.keys():
            unit_keys.extend(load_ns([Content.unit_unprocess(unit, type_id).unit_key for unit in PROFILE.details[type_id].details]))

        print unit_keys
        print units
        for unit in units:
            assert unit.unit_key in unit_keys, 'unit %r not in PROFILE %r' % (unit, PROFILE)
        return method(self, units, options, PROFILE)
    wrapped_method.__name__ = method.__name__
    return wrapped_method



class Task(object):
    '''generic task to perform via gofer-agent dispatch call'''

    def __init__(self, *args, **kvs):
        # store the instantiation call
        self.args = args
        self.kvs = kvs

    def __repr__(self):
        return format_function_call(type(self).__name__, self.args, self.kvs)

class Admin(Task):

    @logged
    def cancel(*args, **kvs):
        return {
           # Dunno what to return here 
        }

class Profile(Task):
    @logged
    def create(self, consumer, content_type='rpm', profile='****'):
        return profile

class Content(Task):
    '''content Task handler'''

    unit_processor = {
        'rpm': (lambda unit: Content.unit_to_nevra(unit), \
            lambda nevra: Content.nevra_to_unit(nevra))
    }

    @classmethod
    def unit_process(cls, unit):
        '''apply given unit processor'''
        return cls.unit_processor[unit.type_id][0](unit)

    @classmethod
    def unit_unprocess(cls, unit, type_id):
        '''apply given unit unprocessor'''
        return cls.unit_processor[type_id][1](unit)

    @staticmethod
    def args_units(*args):
        return load_ns(args[0])

    @staticmethod
    def args_options(*args):
        return load_ns(args[-1])


    @staticmethod
    def unit_to_nevra(request, epoch=0, arch='x86_64', vendor='Fedora'):
        if 'version' in request.unit_key:
            v, r  = request.unit_key.version.split("-")
        else:
            v, r = None, None

        return load_ns({
            'name':  request.unit_key.name,
            'epoch': epoch,
            'version': v,
            'release': r,
            'arch':  arch,
            'vendor': vendor
        })

    @staticmethod
    def nevra_to_unit(nevra):
        return load_ns({
           'type_id': 'rpm',
            'unit_key': {
                'name': nevra.name,
                'version': nevra.version + '-' + nevra.release
            }
        })

    @staticmethod
    def unit_types(units):
        for unit in units:
            assert 'type_id' in unit, 'Unit %r lacks type_id field' % unit
        return set([unit.type_id for unit in units])

    
    @staticmethod
    def dispatch_units(action, units, PROFILE):
        # augment profile with requested unit types
        unit_types = Content.unit_types(units)
        for unit_type in unit_types:
            if unit_type not in PROFILE.details:
                PROFILE.details[unit_type] = load_ns({
                    'details': []
                })

        # dispatch action for all units
        PROFILE.num_changes = len(
            map(
                lambda unit: \
                    action(
                        PROFILE.details[unit.type_id].details,
                        Content.unit_process(unit)
                    ),
                units
            )
        )
        return PROFILE


    @logged
    @content_method
    def install(self, units, options, PROFILE):
        '''dispatch installing new units'''
        return self.dispatch_units(lambda details, unit: details.append(unit), units, PROFILE)

    @logged
    @content_method
    @requires_units
    def update(self, units, options, PROFILE):
        '''dispatch updating units; note that update does nothing :) '''
        return self.dispatch_units(lambda details, unit: None, units, PROFILE)

    @logged
    @content_method
    @requires_units
    def uninstall(self, units, options, PROFILE):
        '''disptach deleting units'''
        return self.dispatch_units(lambda details, unit: details.remove(unit), units, PROFILE)
