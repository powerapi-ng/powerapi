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
Integration test of the Dispatcher Actor

Three level of integration :

level 1 : a dispatcher Actor whith Mocked Handlers

level 2 : a dispatcher Actor With real Handler : ReportHandler and
PoisonPillHandler. The ReportHandler have a mocked HWPCGroupBy Rule

level 3 : a dispatcher Actor With real Handler : ReportHandler and
PoisonPillHandler. The ReportHandler have a real HWPCGroupBy Rule

"""

import pytest
from mock import Mock, patch

from smartwatts.dispatcher import DispatcherActor, RouteTable

####################
## MOCK UTILITIES ##
####################
LOG_FILE = './log'


def init_log():
    f = open(LOG_FILE, 'w+')
    f.close()


def side_effect(a):
    f = open(LOG_FILE, 'a')
    print('ok', file=f)
    f.close()


def count_call():
    f = open(LOG_FILE, 'r')
    i = 0
    for _ in f:
        i += 1
    f.close()
    return i

#################
##   LEVEL 1   ##
#################



# def test_1_create_dispatcher():
#     """
#     Create a dispatcher with mocked message handlers

#     Test if the actor process is alive

#     """

#     with patch('smartwatts.handler.handler.Handler.handle_message', side_effect=side_effect):
#         dispatcher = DispatcherActor('dispatcher', Mock(), Mock(),
#                                      verbose=False)

#         dispatcher.start()
#         assert dispatcher.is_alive()



# def test_1_send_a_msg():
#     """
#     Create a dispatcher with mocked message handler and send it a message it
#     can handle

#     Test if the actor process is alive after sending the message
#     Test if the method MockedHandler.handle_message was call

#     """
#     with patch('smartwatts.handler.handler.Handler.handle_message', side_effect=side_effect):
#         dispatcher = DispatcherActor('dispatcher', Mock(), Mock(),
#                                      verbose=False)

#         dispatcher.start()
#         assert dispatcher.is_alive()
    
#     assert True

# def test_1_send_a_unknow_msg():
#     """
#     Create a dispatcher with mocked message handler and send it a message it
#     can't handle

#     Test if the actor process is alive after sending the message
#     Test if the method MockedHandler.handle_message wasn't call

#     """
#     assert True


#################
##   LEVEL 2   ##
#################


#################
##   LEVEL 3   ##
#################
