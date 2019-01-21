# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
from smartwatts.database.base_db import BaseDB


class StdoutDB(BaseDB):
    """
    StdoutDB class

    This class is mostly use for testing some actor behaviour but
    not very useful.
    """
    def __init__(self):
        pass

    def load(self):
        """
        Override from BaseDB
        """
        pass

    def get_next(self):
        """
        Override from BaseDB
        """
        pass

    def save(self, json):
        """
        Override from BaseDB
        """
        print('['+str(os.getpid())+']' + ' new message save.')
