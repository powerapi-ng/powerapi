# Copyright (c) 2021, Inria
# Copyright (c) 2021, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging
import time

from powerapi.database import MongoDB
from powerapi.message import StartMessage, ErrorMessage, OKMessage
from powerapi.report import PowerReport
from tests.unit.actor.abstract_test_actor import pusher
from tests.utils.db import define_database, define_report_type

URI = "mongodb://localhost:27017"
LOG_LEVEL = logging.NOTSET


def mongodb_database(uri, database_name, collection_name):
    """
    Return MongoDB database
    """
    database = MongoDB(PowerReport, uri, database_name, collection_name)
    return database


##############################################################################
#                          pytest_generate_tests                             #
##############################################################################


def pytest_generate_tests(metafunc):
    """
    Function called by pytest when collecting a test_XXX function

    :param metafunc: the test context given by pytest
    """
    if 'database' in metafunc.fixturenames:
        database = getattr(metafunc.function, '_database', None)
        if isinstance(database, list):
            metafunc.parametrize('database',
                                 [mongodb_database(arg1, arg2, arg3)
                                  for arg1, arg2, arg3 in database])
        else:
            metafunc.parametrize('database', [database])

    if 'report_type' in metafunc.fixturenames:
        report_type = getattr(metafunc.function, '_report_type', None)
        metafunc.parametrize('report_type', [report_type])


##############################################################################
#                                Tests                                       #
##############################################################################
@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_report_type(PowerReport)
def test_create_pusher_and_connect_it_to_mongodb_with_good_config_must_answer_ok_message(pusher, shutdown_system):
    pusher.send_control(StartMessage('system'))
    answer = pusher.receive_control(2000)
    assert isinstance(answer, OKMessage)


@define_database([
    ("mongodb://toto:27017", "test_mongodb", "test_mongodb1"),
    ("mongodb://localhost:27016", "test_mongodb", "test_mongodb1"),
])
@define_report_type(PowerReport)
def test_create_pusher_and_connect_it_to_mongodb_with_bad_config_must_answer_error_message(pusher, shutdown_system):
    pusher.send_control(StartMessage('system'))
    time.sleep(4)
    answer = pusher.receive_control(2000)
    assert isinstance(answer, ErrorMessage)
