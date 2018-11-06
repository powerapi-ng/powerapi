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

    def get_reports_with_sensor(self, sensor):
        """
        Return all reports with this sensor
        """
        raise NotImplementedError

    def load(self):
        """
        Allow to load the database
        """
        raise NotImplementedError
