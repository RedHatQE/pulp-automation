"""
test configuraion facades, roles --- pulp_auto objects
"""

class Facade(object):
    """
    base test configuration --- pulp_auto facade
    """

    @classmethod
    def from_role(cls, role):
        """
        create a facade out of a role
        """
        raise NotImplementedError("%s doesn't implement from_role" % cls.__name__)

    def as_data(self, **override):
        """
        facade as data to feed to pulp_auto objects
        """
        raise NotImplementedError("%s doesn't implement as_data" % self)
