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
  - 1 puller (connected to a database containing 10 hwpc-report, stream mode off)
  - 1 dispatcher (HWPC dispatch rule (dispatch by SOCKET)
  - 1 Dummy Formula
  - 1 pusher (connected to a database)

database content:
  - 10 HWPC Report with two sockets and one RAPL_EVENT

Scenario:
  - Launch the full architecture

Test if:
  - each HWPCReport in the intput database was converted in one PowerReport per
    socket in the output database
"""
import logging
import time
from datetime import datetime

import pytest
import pymongo

from powerapi.database import MongoDB
from powerapi.pusher import PusherActor
from powerapi.formula.dummy import DummyFormulaActor, DummyFormulaValues
from powerapi.supervisor import Supervisor
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.puller import PullerActor
from powerapi.report import HWPCReport
from powerapi.report_model import HWPCModel, PowerModel
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.message import DispatcherStartMessage, FormulaStartMessage
from powerapi.cli.tools import PusherGenerator, PullerGenerator
from powerapi.test_utils.actor import shutdown_system
from powerapi.test_utils.report.hwpc import extract_rapl_reports_with_2_sockets
from powerapi.test_utils.db.mongo import mongo_database
from powerapi.test_utils.db.mongo import MONGO_URI, MONGO_INPUT_COLLECTION_NAME, MONGO_OUTPUT_COLLECTION_NAME, MONGO_DATABASE_NAME
from powerapi.test_utils.db.influx import influx_database, INFLUX_DBNAME, INFLUX_URI, INFLUX_PORT, get_all_reports
from powerapi.test_utils.db.csv import FILES, files, ROOT_PATH, OUTPUT_PATH
from powerapi.test_utils.db.socket import ClientThread, ClientThreadDelay


def filter_rule(msg):
    return True

def launch_simple_architecture(config, supervisor):
    # Pusher
    pusher_generator = PusherGenerator()
    pusher_info = pusher_generator.generate(config)
    pusher_cls, pusher_start_message = pusher_info['test_pusher']
    
    pusher = supervisor.launch(pusher_cls, pusher_start_message)

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel, 'SOCKET'), primary=True))
    dispatcher_start_message = DispatcherStartMessage('system', 'dispatcher', DummyFormulaActor, DummyFormulaValues({'test_pusher': pusher}, 0), route_table, 'cpu')

    dispatcher = supervisor.launch(DispatcherActor, dispatcher_start_message)

    # Puller
    report_filter = Filter()
    report_filter.filter(filter_rule, dispatcher)
    puller_generator = PullerGenerator(report_filter, [])
    puller_info = puller_generator.generate(config)
    puller_cls, puller_start_message = puller_info['test_puller']
    puller = supervisor.launch(puller_cls, puller_start_message)


##################
# MONGO to MONGO #
##################
def check_mongo_db():
    mongo = pymongo.MongoClient(MONGO_URI)
    c_input = mongo[MONGO_DATABASE_NAME][MONGO_INPUT_COLLECTION_NAME]
    c_output = mongo[MONGO_DATABASE_NAME][MONGO_OUTPUT_COLLECTION_NAME]

    assert c_output.count_documents({}) == c_input.count_documents({}) * 2

    for report in c_input.find():
        ts = datetime.strptime(report['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
        assert c_output.count_documents(
            {'timestamp': ts, 'sensor': report['sensor'],
             'target': report['target']}) == 2


@pytest.fixture
def mongodb_content():
    return extract_rapl_reports_with_2_sockets(10)
        
def test_run_mongo(mongo_database, shutdown_system):
    config = {'verbose': True, 'stream': False,
              'output': {'mongodb': {'test_pusher': {'model': 'PowerReport', 'name': 'test_pusher', 'uri': MONGO_URI, 'db': MONGO_DATABASE_NAME, 'collection': MONGO_OUTPUT_COLLECTION_NAME}}},
              'input': {'mongodb': {'test_puller': {'model': 'HWPCReport', 'name': 'test_puller', 'uri': MONGO_URI, 'db': MONGO_DATABASE_NAME, 'collection': MONGO_INPUT_COLLECTION_NAME}}}
              }

    supervisor = Supervisor()
    launch_simple_architecture(config, supervisor)
    supervisor.monitor()

    check_mongo_db()


###################
# MONGO to INFLUX #
###################
@pytest.fixture
def influxdb_content():
    return []

def check_influx_db(influx_client):
    mongo = pymongo.MongoClient(INFLUX_URI)
    c_input = mongo[MONGO_DATABASE_NAME][MONGO_INPUT_COLLECTION_NAME]
    c_output = get_all_reports(influx_client, INFLUX_DBNAME)

    assert c_input.count_documents({}) * 2 == len(c_output)

    for report in c_input.find():
        ts = datetime.strptime(report['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
        influx_client.switch_database(INFLUX_DBNAME)
        # l = list(influx_client.query('SELECT * FROM "power_consumption" WHERE "time" = \'' + report['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ') + '\'').get_points())
        l = list(influx_client.query('SELECT * FROM "power_consumption" WHERE "time" = \'' + report['timestamp'] + 'Z\'').get_points())
        assert len(l) == 2


def test_run_mongo_to_influx(mongo_database, influx_database, shutdown_system):
    config = {'verbose': True, 'stream': False,
              'output': {'influxdb': {'test_pusher': {'model': 'PowerReport', 'name': 'test_pusher', 'uri': INFLUX_URI, 'port': INFLUX_PORT, 'db': INFLUX_DBNAME}}},
              'input': {'mongodb': {'test_puller': {'model': 'HWPCReport', 'name': 'test_puller', 'uri': MONGO_URI, 'db': MONGO_DATABASE_NAME, 'collection': MONGO_INPUT_COLLECTION_NAME}}}
              }

    supervisor = Supervisor()
    launch_simple_architecture(config, supervisor)
    supervisor.monitor()

    check_influx_db(influx_database)


##############
# CSV to CSV #
##############
def check_output_file():
    input_file = open(ROOT_PATH + 'rapl2.csv', 'r')
    output_file = open(OUTPUT_PATH + 'grvingt-12-system/PowerReport.csv', 'r')

    # line count
    l_output = -1
    for _ in output_file:
        l_output += 1

    l_input = -1
    for _ in input_file:
        l_input += 1

    assert l_input == l_output
    output_file.seek(0)
    input_file.seek(0)

    output_file.readline()
    input_file.readline()

    # split socket0 report from socket1 report
    output_socket0 = []
    output_socket1 = []

    for output_line in map(lambda x: x.split(','), output_file):
        if output_line[4] == '\0\n':
            output_socket0.append(output_line)
        else:
            output_socket1.append(output_line)

    input_socket0 = []
    input_socket1 = []
    for input_line in map(lambda x: x.split(','), input_file):
        if input_line[3] == '0':
            input_socket0.append(input_line)
        else:
            input_socket1.append(input_line)

    # check value
    for input_line, output_line in zip(input_socket0 + input_socket1, output_socket0, output_socket1):
        for i in range(3):
            assert input_line[i] == output_line[i]

        assert int(output_line[3]) == 42


def test_run_csv_to_csv(files, shutdown_system):
    config = {'verbose': True, 'stream': False,
              'output': {'csv': {'test_pusher': {'model': 'PowerReport', 'name': 'pusher', 'directory': OUTPUT_PATH}}},
              'input': {'csv': {'test_puller': {'files': FILES, 'model': 'HWPCReport', 'name': 'puller'}}},
              }
    supervisor = Supervisor()
    launch_simple_architecture(config, supervisor)
    supervisor.monitor()
    check_output_file()


################
# SOCKET INPUT #
################
def check_db_socket():
    json_reports = extract_rapl_reports_with_2_sockets(10)
    mongo = pymongo.MongoClient(MONGO_URI)
    c_output = mongo[MONGO_DATABASE_NAME][MONGO_OUTPUT_COLLECTION_NAME]

    assert c_output.count_documents({}) == 20

    for report in json_reports:

        ts = datetime.strptime(report['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
        assert c_output.count_documents(
            {'timestamp': ts, 'sensor': report['sensor'],
             'target': report['target']}) == 2


def test_run_socket_to_mongo(mongo_database, unused_tcp_port, shutdown_system):
    config = {'verbose': True, 'stream': False,
              'output': {'mongodb': {'test_pusher': {'model': 'PowerReport', 'name': 'test_pusher', 'uri': MONGO_URI, 'db': MONGO_DATABASE_NAME,
                                                     'collection': MONGO_OUTPUT_COLLECTION_NAME}}},
              'input': {'socket': {'test_puller': {'port': unused_tcp_port, 'model': 'HWPCReport', 'name': 'puller'}}},
              }
    supervisor = Supervisor()
    launch_simple_architecture(config, supervisor)
    client = ClientThread(extract_rapl_reports_with_2_sockets(10), unused_tcp_port)
    client.start()
    supervisor.monitor()
    check_db_socket()

def test_run_socket_with_delay_between_message_to_mongo(mongo_database, unused_tcp_port, shutdown_system):
    config = {'verbose': True, 'stream': False,
              'output': {'mongodb': {'test_pusher': {'model': 'PowerReport', 'name': 'test_pusher', 'uri': MONGO_URI, 'db': MONGO_DATABASE_NAME,
                                                     'collection': MONGO_OUTPUT_COLLECTION_NAME}}},
              'input': {'socket': {'test_puller': {'port': unused_tcp_port, 'model': 'HWPCReport', 'name': 'test_puller'}}},
              }
    supervisor = Supervisor()
    launch_simple_architecture(config, supervisor)
    client = ClientThreadDelay(extract_rapl_reports_with_2_sockets(10), unused_tcp_port)
    client.start()
    supervisor.monitor()
    check_db_socket()
