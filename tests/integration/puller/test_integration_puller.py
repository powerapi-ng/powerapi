"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import logging
import pickle
import pytest
import random
import zmq
from mock import patch, Mock

from powerapi.filter import Filter, FilterUselessError
from powerapi.report_model import HWPCModel
from powerapi.dispatcher import DispatcherActor
from powerapi.database import BaseDB, MongoDB
from powerapi.puller import PullerActor
from powerapi.report import HWPCReport
from powerapi.backendsupervisor import BackendSupervisor
from powerapi.actor import SafeContext, ActorInitError
from powerapi.message import StartMessage, ErrorMessage
from tests.utils import gen_side_effect
from tests.utils import is_log_ok
from tests.utils import is_actor_alive
from tests.mongo_utils import gen_base_test_unit_mongo
from tests.mongo_utils import clean_base_test_unit_mongo


URI = "mongodb://localhost:27017"
LOG_LEVEL = logging.DEBUG


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


def define_filt(filt):
    """
    Decorator to set the _filt
    attribute for individual tests.
    """
    def wrap(func):
        setattr(func, '_filt', filt)
        return func
    return wrap


##############################################################################
#                                Fixtures                                    #
##############################################################################


@pytest.fixture()
def generate_mongodb_data():
    """
    setup: init and fill the database with data
    teardown: drop collection loaded in database
    """
    gen_base_test_unit_mongo(URI)
    yield
    clean_base_test_unit_mongo(URI)


@pytest.fixture()
def supervisor(database, stream_mode):
    """
    Create a supervisor
    """
    supervisor = BackendSupervisor(stream_mode)
    yield supervisor


@pytest.fixture()
def puller(request, database, filt, stream_mode):
    """
    Setup and Teardown for managing a PullerActor

    setup: create a PullerActor and start its process
    teardown: terminate the PullerActor process
    """
    puller_actor = PullerActor(
        "test_puller_" + str(request.node.name),
        database,
        filt,
        HWPCModel(),
        stream_mode=stream_mode,
        level_logger=LOG_LEVEL)

    yield puller_actor


@pytest.fixture()
def started_puller(puller):
    """
    Return a started PullerActor
    """
    puller.start()
    yield puller
    puller.terminate()
    puller.join()


@pytest.fixture()
def initialized_puller(puller, supervisor):
    """
    Setup PullerActor, send a StartMessage
    """
    supervisor.launch_actor(puller)
    yield puller
    puller.terminate()
    puller.join()


@pytest.fixture()
def initialized_puller_with_dispatcher(puller, supervisor):
    """
    Setup PullerActor, send a StartMessage and handle Dispatcher
    """
    for _, disp in puller.state.report_filter.filters:
        supervisor.launch_actor(disp)

    supervisor.launch_actor(puller)
    yield puller

    for _, disp in puller.state.report_filter.filters:
        disp.terminate()
        disp.join()

    puller.terminate()
    puller.join()


@pytest.fixture()
def initialized_puller_with_dispatcher_plus_supervisor(puller, supervisor):
    """
    Setup PullerActor, send a StartMessage and handle Dispatcher
    """
    for _, disp in puller.state.report_filter.filters:
        supervisor.launch_actor(disp)

    supervisor.launch_actor(puller)
    yield puller, supervisor

    for _, disp in puller.state.report_filter.filters:
        disp.terminate()
        disp.join()

    puller.terminate()
    puller.join()


##############################################################################
#                          objects creations                                 #
##############################################################################


def basic_filt():
    """
    Return a basic filter
    """
    dispatcher = DispatcherActor('dispatcher__', Mock(), Mock())
    filt = Filter()
    filt.filter(lambda msg: True, dispatcher)
    return filt


def empty_filt():
    """
    Return an empty filter
    """
    filt = Filter()
    return filt


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

    if 'filt' in metafunc.fixturenames:
        filt = getattr(metafunc.function, '_filt', None)
        metafunc.parametrize('filt', [filt])

    metafunc.parametrize('stream_mode', [True])


##############################################################################
#                                Tests                                       #
##############################################################################


@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_filt(basic_filt())
def test_puller_create_ok(started_puller):
    """
    Create a PullerActor with a good configuration
    """
    assert is_actor_alive(started_puller)


@define_database([
    ("mongodb://toto:27017", "test_mongodb", "test_mongodb1"),
    ("mongodb://localhost:27016", "test_mongodb", "test_mongodb1"),
])
@define_filt(basic_filt())
def test_puller_create_bad_db(puller, supervisor):
    """
    Create a PullerActor with a bad database
    """
    with pytest.raises(ActorInitError):
        supervisor.launch_actor(puller)
    puller.terminate()
    puller.join()


@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_filt(empty_filt())
def test_puller_create_empty_filter(generate_mongodb_data, supervisor, puller):
    """
    Create a PullerActor with an empty filter
    """
    supervisor.launch_actor(puller)
    assert not is_actor_alive(puller)
    assert isinstance(puller.receive_control(), ErrorMessage)


@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_filt(basic_filt())
def test_puller_init_ok(initialized_puller_with_dispatcher):
    """
    Create a PullerActor and send a StartMessage
    """
    assert is_actor_alive(initialized_puller_with_dispatcher)


@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_filt(basic_filt())
def test_puller_init_already_init(initialized_puller_with_dispatcher):
    """
    Create a PullerActor and send a StartMessage to an already initialized Actor
    """
    initialized_puller_with_dispatcher.send_control(StartMessage())
    assert is_actor_alive(initialized_puller_with_dispatcher)
    assert isinstance(initialized_puller_with_dispatcher.receive_control(), ErrorMessage)


@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_filt(basic_filt())
def test_puller_kill_without_init(started_puller):
    """
    Create a PullerActor and kill him with a PoisonPillMessage before initialization
    """
    started_puller.connect_control()
    started_puller.send_kill()
    assert not is_actor_alive(started_puller)


@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_filt(basic_filt())
def test_puller_kill_after_init(generate_mongodb_data, initialized_puller_with_dispatcher_plus_supervisor):
    """
    Create a PullerActor and kill him with a PoisonPillMessage
    """
    initialized_puller_with_dispatcher_plus_supervisor[1].kill_actors()
    assert not is_actor_alive(initialized_puller_with_dispatcher_plus_supervisor[0])


#def test_puller_reading_ok():
#    """
#    Create a PullerActor and read some data in database with good data
#    """
#    assert False
#
#
#def test_puller_reading_bad_data():
#    """
#    Create a PullerActor and read some data from a db with corrupted data
#    """
#    assert False
