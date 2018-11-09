"""
Module stddb
"""

import os
from smartwatts.database.base_db import BaseDB


class StdoutDB(BaseDB):
    """ StdoutDB class """
    def __init__(self):
        raise NotImplementedError

    def load(self):
        """ Override """
        return

    def get_next(self):
        """ Override """
        return

    def save(self, json):
        """ Override """
        print('['+str(os.getpid())+']' + ' new message save.')
