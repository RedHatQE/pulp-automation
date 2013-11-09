from handler import (Handler, logged, unit_method)
from pulp_auto.namespace import load_ns 
from profile import PROFILE
import logging, yum_unit
log = logging.getLogger(__name__)

class Consumer(Handler):
    '''consumer tasks handler'''

    unit_type_map = {
        'yum_distributor': yum_unit.Distributor
    }

    @logged(log.info)
    @unit_method
    def bind(self, unit_type, unit, PROFILE):
        unit_type.bind(unit, PROFILE)

    @logged(log.info)
    @unit_method
    def unbind(self, unit_type, unit, PROFILE):
        unit_type.unbind(unit, PROFILE)

    @logged(log.info)
    def unregistered(self, *args, **kvs):
        pass

