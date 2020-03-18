# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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
import pytest
import time
from mock import Mock

from powerapi.filter import Filter
from powerapi.report_model import HWPCModel
from powerapi.dispatcher import DispatcherActor
from powerapi.database import MongoDB
from powerapi.puller import PullerActor
from powerapi.backendsupervisor import BackendSupervisor
from powerapi.message import StartMessage, ErrorMessage
from powerapi.actor import ActorInitError
from tests.utils import is_actor_alive
from tests.mongo_utils import gen_base_test_unit_mongo
from tests.mongo_utils import clean_base_test_unit_mongo


URI = "mongodb://localhost:27017"
LOG_LEVEL = logging.NOTSET


##############################################################################
#                            Fixtures utility                                #
##############################################################################
def define_database(database):
    """
    Decorator to set the _database
    attribute for individual tests.
    """
    def wrap(func):
        setattr(func, '_database', database)
        return func
    return wrap


##############################################################################
#                                Fixtures                                    #
##############################################################################
@pytest.fixture()
def supervisor(stream_mode):
    """
    Create a supervisor
    """
    return BackendSupervisor(stream_mode)


@pytest.fixture()
def puller(request, database, stream_mode):
    """
    Setup and Teardown for managing a PullerActor

    setup: create a PullerActor and start its process
    teardown: terminate the PullerActor process
    """
    dispatcher = DispatcherActor('dispatcher__', Mock(), Mock())
    filt = Filter()
    filt.filter(lambda msg: True, dispatcher)

    puller_actor = PullerActor(
        "test_puller_" + str(request.node.name),
        database,
        filt,
        HWPCModel(),
        stream_mode=stream_mode,
        level_logger=LOG_LEVEL)

    return puller_actor


@pytest.fixture()
def started_puller(puller):
    """
    Return a started PullerActor
    """
    puller.start()
    yield puller
    puller.terminate()
    puller.join()


##############################################################################
#                          objects creations                                 #
##############################################################################
def mongodb_database(uri, database_name, collection_name):
    """
    Return MongoDB database
    """
    database = MongoDB(uri, database_name, collection_name)
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

    metafunc.parametrize('stream_mode', [True])


##############################################################################
#                                Tests                                       #
##############################################################################
@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
def test_puller_create_ok(started_puller):
    """
    Create a PullerActor with a good configuration
    """
    assert is_actor_alive(started_puller)


@define_database([
    ("mongodb://toto:27017", "test_mongodb", "test_mongodb1"),
    ("mongodb://localhost:27016", "test_mongodb", "test_mongodb1"),
])
def test_puller_create_bad_db(puller, supervisor):
    """
    Create a PullerActor with a bad database
    """
    with pytest.raises(ActorInitError):
        supervisor.launch_actor(puller)
    puller.terminate()
    puller.join()
