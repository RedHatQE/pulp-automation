import rpm_unit, profile, logging
from pulp.namespace import load_ns
from handler import (Handler, logged, unit_method)

log = logging.getLogger(__name__)

class Content(Handler):
    '''content Task handler'''

    unit_type_map = {
        'rpm': rpm_unit.Rpm
    }

    @classmethod
    def augment_profile(cls, units, PROFILE):
        # augment profile with requested unit types
        cls.assert_units(units)
        for unit_type in cls.unit_types(units):
            if unit_type not in PROFILE.details:
                # different structure for content details
                PROFILE.details[unit_type] = load_ns({
                    'details': []
                })

    @logged(log.info)
    @unit_method
    def install(self, unit_type, unit, PROFILE):
        '''dispatch installing new units'''
        unit_type.store(unit, PROFILE)

    @logged(log.info)
    @unit_method
    def update(self, unit_type, unit, PROFILE):
        '''dispatch updating units'''
        unit_type.update(unit, PROFILE)

    @logged(log.info)
    @unit_method
    def uninstall(self, unit_type, unit, PROFILE):
        '''disptach removing units'''
        unit_type.remove(unit, PROFILE) 
