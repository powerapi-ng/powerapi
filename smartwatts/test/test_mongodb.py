"""
Module test db
"""

import sys
import os
import pytest

from smartwatts.db.db import Database
from smartwatts.db.base_db import MissConfigParamError

PATH_TO_TEST = "/smartwatts/test/"


class TestDatabase():
    """ Test class of Database class """

    MISS_CONFIG_PARAM_FILES = [
        "./data_test/conf_wo_collection.json",
        "./data_test/conf_wo_db.json",
        "./data_test/conf_wo_host.json",
        "./data_test/conf_wo_port.json",
        "./data_test/conf_wo_type.json"
        ]

    def test_mongodb_miss_config_param(self):
        """ Test open config with missing param """
        for filename in self.MISS_CONFIG_PARAM_FILES:
            with pytest.raises(MissConfigParamError) as pytest_wrapped:
                Database(os.getcwd() + PATH_TO_TEST + filename)
            assert pytest_wrapped.type == MissConfigParamError
