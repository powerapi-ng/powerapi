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
import pytest

from powerapi.report_model import PowerModel
from powerapi.database import MongoDB
from powerapi.pusher import PusherActor
from powerapi.report import PowerReport
from powerapi.backendsupervisor import BackendSupervisor
from powerapi.message import StartMessage, ErrorMessage
from powerapi.actor import ActorInitError
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


def define_report_model(report_model):
    """
    Decorator to set the _report_model
    attribute for individuel tests.
    """
    def wrap(func):
        setattr(func, '_report_model', report_model)
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
def supervisor(database):
    """
    Create a supervisor
    """
    supervisor = BackendSupervisor(True)
    yield supervisor


@pytest.fixture()
def pusher(request, database, report_model):
    """
    Setup and Teardown for managing a PusherActor

    setup: create a PusherActor and start its process
    teardown: terminate the PusherActor process
    """
    pusher_actor = PusherActor(
        "test_pusher_" + str(request.node.name),
        report_model,
        database,
        level_logger=LOG_LEVEL)

    yield pusher_actor


@pytest.fixture()
def started_pusher(pusher):
    """
    Return a started PusherActor
    """
    pusher.start()
    yield pusher
    pusher.terminate()
    pusher.join()


@pytest.fixture()
def initialized_pusher(pusher, supervisor):
    """
    Setup PusherActor, send a StartMessage
    """
    supervisor.launch_actor(pusher)
    yield pusher
    pusher.terminate()
    pusher.join()


@pytest.fixture()
def initialized_pusher_plus_supervisor(pusher, supervisor):
    """
    Setup PusherActor, send a StartMessage
    """
    supervisor.launch_actor(pusher)
    yield pusher, supervisor
    pusher.terminate()
    pusher.join()


##############################################################################
#                          objects creations                                 #
##############################################################################
#
#
#def basic_filt():
#    """
#    Return a basic filter
#    """
#    dispatcher = DispatcherActor('dispatcher__', Mock(), Mock())
#    filt = Filter()
#    filt.filter(lambda msg: True, dispatcher)
#    return filt
#
#
#def empty_filt():
#    """
#    Return an empty filter
#    """
#    filt = Filter()
#    return filt


def gen_power_report():
    return PowerReport(1, "sensor", "target", 0.11, {"metadata1": "truc", "metadata2": "oui"})


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

    if 'report_model' in metafunc.fixturenames:
        report_model= getattr(metafunc.function, '_report_model', None)
        metafunc.parametrize('report_model',
                              [report_model])


##############################################################################
#                                Tests                                       #
##############################################################################


@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_report_model(PowerModel())
def test_pusher_create_ok(started_pusher):
    """
    Create a PusherActor with a good configuration
    """
    assert is_actor_alive(started_pusher)


@define_database([
    ("mongodb://toto:27017", "test_mongodb", "test_mongodb1"),
    ("mongodb://localhost:27016", "test_mongodb", "test_mongodb1"),
])
@define_report_model(PowerModel())
def test_pusher_create_bad_db(pusher, supervisor):
    """
    Create a PusherActor with a bad database
    """
    with pytest.raises(ActorInitError):
        supervisor.launch_actor(pusher)
    pusher.terminate()
    pusher.join()


@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_report_model(PowerModel())
def test_pusher_init_ok(initialized_pusher):
    """
    Create a PusherActor and send a StartMessage
    """
    assert is_actor_alive(initialized_pusher)


@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_report_model(PowerModel())
def test_pusher_init_already_init(initialized_pusher):
    """
    Create a PusherActor and send a StartMessage to an already initialized Actor
    """
    initialized_pusher.send_control(StartMessage())
    assert is_actor_alive(initialized_pusher)
    assert isinstance(initialized_pusher.receive_control(), ErrorMessage)


@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_report_model(PowerModel())
def test_pusher_kill_without_init(started_pusher):
    """
    Create a PusherActor and kill him with a PoisonPillMessage before initialization
    """
    started_pusher.connect_data()
    started_pusher.send_kill(by_data=True)
    assert not is_actor_alive(started_pusher, 5)


@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb1"))
@define_report_model(PowerModel())
def test_pusher_kill_after_init(generate_mongodb_data, initialized_pusher_plus_supervisor):
    """
    Create a PusherActor and kill him with a PoisonPillMessage
    """
    initialized_pusher_plus_supervisor[1].kill_actors()
    assert not is_actor_alive(initialized_pusher_plus_supervisor[0])


# TODO: Test with different config:
# - Type of report
# - Stream mode or not
# - Type of database
@define_database(mongodb_database(URI, "test_mongodb", "test_mongodb_pr"))
@define_report_model(PowerModel())
def test_pusher_save_power_report(generate_mongodb_data, initialized_pusher):
    """
    Create a PusherActor, send him a PowerReport, kill him and check it from database
    """
    # Connect data and send a PowerReport
    initialized_pusher.connect_data()
    saved_report = gen_power_report()
    initialized_pusher.send_data(saved_report)

    # Kill it
    initialized_pusher.send_kill(by_data=True)
    assert not is_actor_alive(initialized_pusher, 5)

    # Open a database for read the saved report
    mongodb = initialized_pusher.state.database
    mongodb.connect()
    mongodb_iter = mongodb.iter(PowerModel(), False)
    new_report = next(mongodb_iter)

    assert saved_report == new_report
