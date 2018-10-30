"""
Module test db
"""

import sys
import os
import pytest

from smartwatts.db.db import Database, UnknownDatabaseTypeError
from smartwatts.db.base_db import MissConfigParamError

PATH_TO_TEST = "/smartwatts/test/"


class TestDatabase():
    """ Test class of Database class """

    def test_open_unknown_file(self):
        """ Test open unknow file """
        with pytest.raises(SystemExit) as pytest_wrapped:
            Database(os.getcwd() + PATH_TO_TEST +
                     './data_test/unknown_file.json')
        assert pytest_wrapped.type == SystemExit

    def test_unknown_db_type(self):
        """ Test unknown db type """
        with pytest.raises(UnknownDatabaseTypeError) as pytest_wrapped:
            Database(os.getcwd() + PATH_TO_TEST +
                     './data_test/conf_unknown_type.json')
        assert pytest_wrapped.type == UnknownDatabaseTypeError
