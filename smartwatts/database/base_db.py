"""
Module base_db which define every common function
that need to be implemented by each DB module
"""


class BaseDB:
    """
    BaseDB class.

    JSON HWPC format:
    {
     'timestamp': $int,
     'sensor': '$str',
     'target': '$str',
     'groups' : {
        '$group_name': {
           '$socket_id': {
               '$core_id': {
                   '$event_name': '$int',
                   ...
               }
               ...
           }
           ...
        }
        ...
     }
    }
    """
    def load(self):
        """
        Allow to load the database
        """
        raise NotImplementedError

    def get_next(self):
        """
        Return the next report on the db
        """
        raise NotImplementedError
