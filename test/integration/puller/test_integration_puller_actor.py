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

import pytest
import zmq
from mock import patch, Mock

from powerapi.message import OKMessage, StartMessage, ErrorMessage
from powerapi.filter import Filter
from powerapi.dispatcher import DispatcherActor
from powerapi.database import BaseDB, MongoDB
from powerapi.puller import PullerActor
from powerapi.actor import Actor
from test.integration.integration_utils import *

SOCKET_ADDRESS = 'ipc://@test_puller'


@pytest.fixture()
def context():
    """
    Get ZMQ context
    """
    return zmq.Context()

##################
# Initialisation #
##################


@patch('powerapi.database.base_db.BaseDB.load',
       side_effect=gen_side_effect(SOCKET_ADDRESS, "load"))
@patch('powerapi.puller.puller_actor.PullerActor._read_behaviour',
       side_effect=Actor._initial_behaviour)
@patch('powerapi.dispatcher.dispatcher_actor.DispatcherActor.connect_data',
       side_effect=gen_side_effect(SOCKET_ADDRESS, 'connect_data'))
def test_start_msg_db_ok(a, b, c, context):
    """
    Send a start message to a PullerActor

    After sending the message test :
      - if the actor is alive
      - if the init method of the database object was called
      - if the actor send a OkMessage to the test process
      - if the actor call the dispatcher.connect method
    """

    database = BaseDB(Mock())
    dispatcher = DispatcherActor('dispatcher_test', Mock(), Mock())
    filt = Filter()
    filt.filter(lambda msg: True, dispatcher)

    puller = PullerActor("puller_test", database, filt, 0, timeout=500)
    puller.start()
    puller.connect_control(context)

    puller.send_control(StartMessage())
    assert is_log_ok(SOCKET_ADDRESS, ['load', 'connect_data'], context)
    assert puller.is_alive()
    assert isinstance(puller.receive_control(), OKMessage)

    puller.kill()

#################
# Mongo DB Test #
#################


def test_start_msg_db_bad_hostname(context):
    """
    Send a start message to a PullerActor with a DB with a bad configuration

    After sending the message test :
      - if the actor is alive
      - if the init method of the database object was called
      - if the actor send a OkMessage to the test process
      - if the actor call the dispatcher.connect method
    """

    database = MongoDB('toto', 27017, 'test_mongodb', 'test_monggodb1',
                       report_model=Mock())

    puller = PullerActor("puller_test", database, Mock(), 0, timeout=500)
    puller.start()
    puller.connect_control(context)

    puller.send_control(StartMessage())
    puller.join()
    assert not puller.is_alive()
    assert isinstance(puller.receive_control(), ErrorMessage)
