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
"""
Integration test of the puller actor
"""

import logging
import os
import pickle
import pytest
import zmq
from mock import patch, Mock

from powerapi.message import OKMessage, StartMessage, ErrorMessage
from powerapi.message import PoisonPillMessage
from powerapi.filter import Filter
from powerapi.report_model import HWPCModel
from powerapi.dispatcher import DispatcherActor
from powerapi.database import BaseDB, MongoDB
from powerapi.puller import PullerActor
from powerapi.report import HWPCReport
from powerapi.actor import Actor, Supervisor
from powerapi.actor import SafeContext, ActorInitError
from test.utils import gen_side_effect
from test.utils import is_log_ok
from test.utils import gen_send_side_effect
from test.utils import receive_side_effect
from test.utils import is_actor_alive
from test.integration.puller.fake_dispatcher import FakeDispatcherActor
from test.mongo_utils import gen_base_test_unit_mongo
from test.mongo_utils import clean_base_test_unit_mongo


URI = "mongodb://localhost:27017"
FILENAME = 'test_puller_file.csv'
DISPATCHER_SOCKET_ADDRESS = "ipc://@test_dispatcher_socket"
LOG_LEVEL = logging.NOTSET

##############################################################################
#                                Fixtures utility                            #
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


def define_stream_mode(stream_mode):
    """
    Decorator to set the _stream_mode
    attribute for individual tests.
    """
    def wrap(func):
        setattr(func, '_stream_mode', stream_mode)
        return func
    return wrap


def receive(socket):
    """
    wait for a message reception on a given socket and return it
    return None if no message was receive until 500ms
    """
    event = socket.poll(500)
    if event == 0:
        return None
    return pickle.loads(socket.recv())


##############################################################################
#                                Fixtures                                    #
##############################################################################


@pytest.fixture()
def generate_mongodb_data():
    """
    setup : init and fill the database with data
    teardown : drop collection loaded in database
    """
    gen_base_test_unit_mongo(URI)
    yield
    clean_base_test_unit_mongo(URI)


@pytest.fixture()
def log_file():
    """
    Get log file
    """
    with open(FILENAME, 'w') as f:
        f.close()

    with open(FILENAME, 'r') as f:
        yield f
        f.close()

    if os.path.exists(FILENAME):
        os.remove(FILENAME)


@pytest.fixture()
def dispatcher_socket():
    """
    return the socket that will be used by the FakeDispatcherActor
    to log their actions
    """
    socket = SafeContext.get_context().socket(zmq.PULL)
    socket.bind(DISPATCHER_SOCKET_ADDRESS)
    yield socket
    socket.close()


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
        level_logger=LOG_LEVEL,
        stream_mode=stream_mode)

    yield puller_actor

@pytest.fixture()
def supervisor():
    """
    Create a supervisor
    """
    supervisor = Supervisor()
    yield supervisor


@pytest.fixture()
def initialized_puller(puller, supervisor):
    """
    Setup PullerActor and send a StartMessage to the PullerActor
    """
    supervisor.launch_actor(puller)
    yield puller
    puller.state.socket_interface.close()
    puller.terminate()
    puller.join()


@pytest.fixture()
def initialized_puller_with_dispatcher(initialized_puller, supervisor):
    """
    Setup PullerActor, send a StartMessage and handle Dispatcher
    """

    for _, disp in initialized_puller.state.report_filter.filters:
        supervisor.launch_actor(disp)

    yield initialized_puller

    for _, disp in initialized_puller.state.report_filter.filters:
        disp.state.socket_interface.close()
        disp.terminate()
        disp.join()


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


def fake_dispatcher_filt():
    """
    Return a filter that dispatch to a fake dispatcher
    """
    dispatcher = FakeDispatcherActor('fake_dispatcher__',
                                     DISPATCHER_SOCKET_ADDRESS,
                                     level_logger=LOG_LEVEL)
    filt = Filter()
    filt.filter(lambda msg: True, dispatcher)
    return filt


def mocked_database():
    """
    Return a BaseDB mocked object
    """
    return BaseDB(Mock())


def mongodb_database(uri, database_name, collection_name):
    """
    Return MongoDB database
    """
    database = MongoDB(uri, database_name, collection_name,
                       HWPCModel())
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

    if 'stream_mode' in metafunc.fixturenames:
        stream_mode = getattr(metafunc.function, '_stream_mode', None)
        if stream_mode == 'both':
            metafunc.parametrize('stream_mode', [True, False])
        else:
            metafunc.parametrize('stream_mode', [stream_mode])


##############################################################################
#                                Tests                                       #
##############################################################################


class TestPuller:

    @pytest.fixture(autouse=True)
    def basedb_mocked_connect(self):
        with patch('powerapi.database.base_db.BaseDB.connect',
                   side_effect=gen_side_effect(FILENAME, 'connect')):
            yield

    @pytest.fixture(autouse=True)
    def basedb_mocked_iter(self):
        with patch('powerapi.database.base_db.BaseDB.__iter__',
                   side_effect=lambda: iter([])):
            yield

    @pytest.fixture(autouse=True)
    def basedb_mocked_next(self):
        with patch('powerapi.database.base_db.BaseDB.__next__',
                   side_effect=StopIteration()):
            yield

    @pytest.fixture(autouse=True)
    def dispatcher_mocked_connect_data(self):
        with patch('powerapi.dispatcher.dispatcher_actor.DispatcherActor.connect_data',
                   side_effect=gen_side_effect(FILENAME, 'connect_data')):
            yield

    @pytest.fixture(autouse=True)
    def dispatcher_mocked_send_kill(self):
        with patch('powerapi.dispatcher.dispatcher_actor.DispatcherActor.send_kill',
                   side_effect=gen_side_effect(FILENAME, 'send_kill')):
            yield

    #################
    #      Init     #
    #################

    @define_database(mocked_database())
    @define_filt(basic_filt())
    @define_stream_mode(False)
    def test_start_msg_db_ok(self, log_file, initialized_puller):
        """
        Send a start message to a PullerActor

        After sending the message test :
          - if the actor send a OkMessage to the test process
          - if the actor is dead
          - if the following method has been called:
            - connect from database
            - connect_data from dispatcher
            - send_kill
        """
        assert not is_actor_alive(initialized_puller)
        assert is_log_ok(log_file,
                         ['connect', 'connect_data', 'send_kill'])

    @define_database(mocked_database())
    @define_filt(basic_filt())
    @define_stream_mode(True)
    def test_start_msg_db_ok_stream(self, log_file, initialized_puller):
        """
        Send a start message to a PullerActor with stream mode on

        After sending the message test :
          - if the actor send a OkMessage to the test process
          - if the actor is alive
          - if the following method has been called:
            - connect from database
            - connect_data from dispatcher
        """
        assert initialized_puller.is_alive()
        assert is_log_ok(log_file,
                         ['connect', 'connect_data'])

    #################
    #      Kill     #
    #################

    @define_database(mocked_database())
    @define_filt(basic_filt())
    @define_stream_mode(True)
    def test_puller_kill_init(self, initialized_puller):
        """
        Create an initialized Puller and call its kill method

        Test if:
         - Actor is terminated
        """
        initialized_puller.send_kill()
        assert not is_actor_alive(initialized_puller)


@define_database(mongodb_database(URI,
                                  "test_mongodb", "test_mongodb1"))
@define_filt(fake_dispatcher_filt())
@define_stream_mode(True)
def test_puller_kill_with_dispatcher(initialized_puller_with_dispatcher):
    """
    Create an initialized Puller and call its kill method

    Test if:
     - Actor is terminated
     - Disconnect from Dispatchers
    """
    initialized_puller_with_dispatcher.send_kill()
    assert not is_actor_alive(initialized_puller_with_dispatcher)
    for _, disp in initialized_puller_with_dispatcher.state.report_filter.filters:
        assert not is_actor_alive(disp)

#################
# Mongo DB Test #
#################


@define_database([
    ("mongodb://toto:27017", "test_mongodb", "test_mongodb1"),
    ("mongodb://localhost:27016", "test_mongodb", "test_mongodb1"),
    ])
@define_filt(basic_filt())
@define_stream_mode('both')
def test_mongodb_bad_config(puller, supervisor):
    """
    Send a start message to a PullerActor with a DB with a bad configuration

    After sending the message test :
      - if the actor send an ErrorMessage to the test process
      - if the actor is dead
    """
    with pytest.raises(ActorInitError):
        supervisor.launch_actor(puller)
    assert not is_actor_alive(puller)


@define_database(mongodb_database(URI,
                                  "test_mongodb", "test_mongodb1"))
@define_filt(fake_dispatcher_filt())
@define_stream_mode(True)
def test_mongodb_reading_data(generate_mongodb_data,
                              initialized_puller_with_dispatcher,
                              dispatcher_socket):
    """
    Send a start message to a PullerActor with a MongoDB
    And test if reading data is ok

    After sending the message test :
      - if the actor is alive
      - if the actor send a OkMessage to the test process
      - if dispatcher receive data
    """

    assert initialized_puller_with_dispatcher.is_alive()
    for _ in range(10):
        assert isinstance(receive(dispatcher_socket), HWPCReport)