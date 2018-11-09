"""
Module base_db

This module define every common function that need to be implemented
by each DB module. A database module correspond to a kind of BDD.
For example, Mongodb, influxdb, csv are different kind of BDD.
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
        Return the next report on the db or none if there is none
        """
        raise NotImplementedError

    def save(self, json):
        """
        Allow to save a json input in the db
        """
        raise NotImplementedError
