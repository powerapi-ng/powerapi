"""
Module base_db which define every common function
that need to be implemented by each DB module
"""


class MissConfigParamError(Exception):
    """ Exception """
    pass


class BaseDB:
    """
    BaseDB class.
    """

    def get_last_hwpc_report(self):
        """
        Return the last hwpc report in the base
        """
        raise NotImplementedError
