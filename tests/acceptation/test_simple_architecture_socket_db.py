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


"""
Test the behaviour of the most simple architecture

Architecture :
  - 1 puller (socketDB) connected to a client that send him hwpc report by a socket, stream mode on
  - 1 dispatcher (HWPC dispatch rule (dispatch by SOCKET)
  - 1 Dummy Formula
  - 1 pusher (connected to MongoDB1 [collection test_result]

Client send:
  - 10 HWPC Report with one sockets and one RAPL_EVENT


Scenario:
  - Launch the full architecture

Test if:
  - each HWPCReport sent by the client was converted in one PowerReport per
    socket in the output database
"""

import json
import time
import logging
import random
from threading import Thread
from socket import socket

import pytest
import pymongo

from powerapi.database import MongoDB, SocketDB
from powerapi.pusher import PusherActor
from powerapi.backendsupervisor import BackendSupervisor
from powerapi.formula import DummyFormulaActor
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.puller import PullerActor
from powerapi.report import HWPCReport
from powerapi.report_model import HWPCModel, PowerModel
from powerapi.dispatcher import DispatcherActor, RouteTable


from tests.mongo_utils import gen_base_db_test
from tests.mongo_utils import clean_base_db_test

DB_URI = "mongodb://localhost:27017/"
LOG_LEVEL = logging.NOTSET


@pytest.fixture
def database():
    db = gen_base_db_test(DB_URI, 0)
    yield db
    clean_base_db_test(DB_URI)

@pytest.fixture
def supervisor():
    s = BackendSupervisor(True)
    yield s
    s.kill_actors()

def extract_json_report(n):
    json_file = open('tests/hwpc_reports.json', 'r')
    reports = json.load(json_file)
    json_file.close()
    return reports['reports'][:n]

class ClientThread(Thread):

    def __init__(self, msg_list, port):
        Thread.__init__(self)

        self.msg_list = msg_list
        self.socket = socket()
        self.port = port

    def run(self):

        self.socket.connect(('localhost', self.port))
        for msg in self.msg_list:
            self.socket.send(bytes(json.dumps(msg), 'utf-8'))
        self.socket.close()

class ClientThreadDelay(Thread):

    def __init__(self, msg_list, port):
        Thread.__init__(self)

        self.msg_list = msg_list
        self.socket = socket()
        self.port = port

    def run(self):

        self.socket.connect(('localhost', self.port))
        midle = int(len(self.msg_list) / 2)
        for msg in self.msg_list[:midle]:
            self.socket.send(bytes(json.dumps(msg), 'utf-8'))
        time.sleep(1)
        for msg in self.msg_list[midle:]:
            self.socket.send(bytes(json.dumps(msg), 'utf-8'))
        self.socket.close()


def check_db():
    json_reports = extract_json_report(10)
    mongo = pymongo.MongoClient(DB_URI)
    c_output = mongo['MongoDB1']['test_result']

    assert c_output.count_documents({}) == 10

    for report in json_reports:

        assert c_output.count_documents(
            {'timestamp': report['timestamp'], 'sensor': report['sensor'],
             'target': report['target']}) == 1


def test_run(database, supervisor, unused_tcp_port):
    # Pusher
    output_mongodb = MongoDB(DB_URI, 'MongoDB1', 'test_result')
    pusher = PusherActor("pusher_mongodb", PowerModel(), output_mongodb, level_logger=LOG_LEVEL, max_size=0)

    # Formula
    formula_factory = (lambda name, verbose:
                       DummyFormulaActor(name, {'my_pusher': pusher}, level_logger=verbose))

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'SOCKET'), primary=True))

    dispatcher = DispatcherActor('dispatcher', formula_factory, route_table, level_logger=LOG_LEVEL)

    # Puller
    input_socket = SocketDB(unused_tcp_port)
    report_filter = Filter()
    report_filter.filter(lambda msg: True, dispatcher)
    puller = PullerActor("puller_socket", input_socket, report_filter, HWPCModel(), level_logger=LOG_LEVEL, stream_mode=True)
    supervisor.launch_actor(pusher)
    supervisor.launch_actor(dispatcher)
    supervisor.launch_actor(puller)
    time.sleep(1)
    json_reports = extract_json_report(10)
    client = ClientThread(json_reports, unused_tcp_port)
    client.start()
    time.sleep(1)
    check_db()

def test_run_with_delay_between_message(unused_tcp_port, database, supervisor):
    """
    run the same test but set a delay of 1s after sendig the 5th first messages
    """
    # Pusher
    output_mongodb = MongoDB(DB_URI, 'MongoDB1', 'test_result')
    pusher = PusherActor("pusher_mongodb", PowerModel(), output_mongodb, level_logger=LOG_LEVEL, max_size=0)

    # Formula
    formula_factory = (lambda name, verbose:
                       DummyFormulaActor(name, {'my_pusher': pusher}, level_logger=verbose))

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'SOCKET'), primary=True))

    dispatcher = DispatcherActor('dispatcher', formula_factory, route_table, level_logger=LOG_LEVEL)

    # Puller
    input_socket = SocketDB(unused_tcp_port)
    report_filter = Filter()
    report_filter.filter(lambda msg: True, dispatcher)
    puller = PullerActor("puller_socket", input_socket, report_filter, HWPCModel(), level_logger=LOG_LEVEL, stream_mode=True)
    supervisor.launch_actor(pusher)
    supervisor.launch_actor(dispatcher)
    supervisor.launch_actor(puller)
    time.sleep(1)
    json_reports = extract_json_report(10)
    client = ClientThreadDelay(json_reports, unused_tcp_port)
    client.start()
    time.sleep(2)
    check_db()
