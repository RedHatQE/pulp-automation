import rpm_unit, profile, logging
from pulp.namespace import load_ns
from handler import (Handler, logged)

log = logging.getLogger(__name__)

def content_method(method):
    '''maps a method on all the units;
    *args -> units, options; **kvs -> PROFILE;
    return PROFILE
    '''
    def wrapped_method(self, *args, **kvs):
        units = args[0]
        options = args[-1]
        # if there is no PROFILE in kvs, use a PROFILE copy from this module
        PROFILE = kvs.pop('PROFILE', profile.PROFILE.copy())
        Content.augment_profile(units, PROFILE)
        # map the method on all the units
        PROFILE.num_changes = len(
            map(
                lambda unit: \
                    method(
                            self,
                            Content.unit_type[unit.type_id],
                            unit,
                            PROFILE
                    ),
                units
            )
        )
        return PROFILE 
    wrapped_method.__name__ = method.__name__
    return wrapped_method

class Content(Handler):
    '''content Task handler'''

    unit_type = {
        'rpm': rpm_unit.Rpm
    }

    @staticmethod
    def assert_units(units):
        for unit in units:
            assert 'type_id' in unit, 'Unit %r lacks type_id field' % unit
            assert unit.type_id in Content.unit_type, 'Unkown unit type: %r' % unit
        
    @staticmethod
    def unit_types(units):
        return set([unit.type_id for unit in units])

    
    @staticmethod
    def augment_profile(units, PROFILE):
        # augment profile with requested unit types
        Content.assert_units(units)
        for unit_type in Content.unit_types(units):
            if unit_type not in PROFILE.details:
                PROFILE.details[unit_type] = load_ns({
                    'details': []
                })

    @logged
    @content_method
    def install(self, unit_type, unit, PROFILE):
        '''dispatch installing new units'''
        unit_type.store(unit, PROFILE)

    @logged
    @content_method
    def update(self, unit_type, unit, PROFILE):
        '''dispatch updating units'''
        unit_type.update(unit, PROFILE)

    @logged
    @content_method
    def uninstall(self, unit_type, unit, PROFILE):
        '''disptach removing units'''
        unit_type.remove(unit, PROFILE) 
        

    @logged
    def profile(self, *args, **kvs):
        _PROFILE = kvs.pop('PROFILE', PROFILE.copy())
        _PROFILE.num_changes = 0
        return _PROFILE
