from pulp_auto.namespace import load_ns, Namespace


class Rpm(object):
    '''rpm-specific content type actions'''
    @staticmethod
    def unit_to_nevra(request, epoch=0, arch='x86_64', vendor='Fedora'):
        # unit key as in https://pulp.readthedocs.org/en/latest/dev-guide/integration/rest-api/consumer/content.html#install-content-on-a-consumer
        assert type(request.unit_key) is Namespace, 'unsupported unit key type: %s' % type(request.unit_key)
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
    def list(unit, PROFILE, filter_method=lambda unit, nevra: unit.name == nevra.name):
        nevra = Rpm.unit_to_nevra(unit)
        return filter(lambda unit: filter_method(unit, nevra), PROFILE.details.rpm.details)

    @staticmethod
    def remove(unit, PROFILE):
        map (
            lambda unit: PROFILE.details.rpm.details.remove(unit),
            Rpm.list(unit, PROFILE)
        )

    @staticmethod
    def store(unit, PROFILE):
        if Rpm.list(unit, PROFILE) == []:
            PROFILE.details.rpm.details.append(Rpm.unit_to_nevra(unit))

    @staticmethod
    def update(unit, PROFILE):
        '''note that update does nothing :) '''
        if Rpm.list(unit, PROFILE) == []:
            raise ValueError("%r not found in PROFILE" % unit)
 
