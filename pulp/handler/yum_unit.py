from pulp.namespace import load_ns

class Distributor(object):
    '''yum-specific consumer actions'''

    @staticmethod
    def list(unit, PROFILE, filter_method=lambda unit_a, unit_b : unit_a.repo_id == unit_b.repo_id):
        return filter(lambda unit_x: filter_method(unit, unit_x), PROFILE.details.yum_distributor)

    @staticmethod
    def bind(unit, PROFILE):
        assert Distributor.list(unit, PROFILE) == [], 'unit %s already bound' % unit
        PROFILE.details.yum_distributor.append(unit)

    @staticmethod
    def unbind(unit, PROFILE):
        units = Distributor.list(unit, PROFILE)
        assert units != [], 'unit %s not found in profile' % unit
        map(lambda unit: PROFILE.details.yum_distributor.remove(unit), units)


            
