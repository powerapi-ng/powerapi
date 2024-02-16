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

import time
from datetime import datetime

import pymongo
import pytest

from powerapi.actor import Supervisor
from tests.utils.acceptation import launch_simple_architecture, BASIC_CONFIG, SOCKET_DEPTH_LEVEL, \
    CSV_INPUT_OUTPUT_CONFIG
from tests.utils.db.csv import ROOT_PATH, OUTPUT_PATH
from tests.utils.db.mongo import MONGO_URI, MONGO_INPUT_COLLECTION_NAME, MONGO_OUTPUT_COLLECTION_NAME, \
    MONGO_DATABASE_NAME
from tests.utils.db.socket import ClientThread, ClientThreadDelay
from tests.utils.formula.dummy import DummyFormulaActor
from tests.utils.report.hwpc import extract_rapl_reports_with_2_sockets


##################
# MONGO to MONGO #
##################
def check_mongo_db():
    """
        Verify that output DB has the correct information
    """
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
    """
        Get reports from a file for testing purposes
    """
    return extract_rapl_reports_with_2_sockets(51)


def test_run_mongo(mongo_database):
    """
        Check that report are correctly stored into an output mongo database.
        The input source is also a mongo database
    """
    supervisor = Supervisor()
    launch_simple_architecture(config=BASIC_CONFIG, supervisor=supervisor, hwpc_depth_level=SOCKET_DEPTH_LEVEL,
                               formula_class=DummyFormulaActor)

    time.sleep(2)
    check_mongo_db()

    supervisor.kill_actors()


###################
# MONGO to INFLUX #
###################
@pytest.fixture
def influxdb_content():
    """
        Return an empty content for an influxdb
    """
    return []


##############
# CSV to CSV #
##############
def check_output_file():
    """
         Verify that output file has the correct information
    """
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
    """
        Check that report are correctly stored into an output file.
        The input source is a CSV file
    """
    supervisor = Supervisor()
    launch_simple_architecture(config=CSV_INPUT_OUTPUT_CONFIG, supervisor=supervisor,
                               hwpc_depth_level=SOCKET_DEPTH_LEVEL,
                               formula_class=DummyFormulaActor)

    time.sleep(2)

    check_output_file()

    supervisor.kill_actors()


################
# SOCKET INPUT #
################
def check_db_socket():
    """
         Verify that output DB has the correct information
    """
    time.sleep(6)
    json_reports = extract_rapl_reports_with_2_sockets(10)
    mongo = pymongo.MongoClient(MONGO_URI)
    c_output = mongo[MONGO_DATABASE_NAME][MONGO_OUTPUT_COLLECTION_NAME]

    assert c_output.count_documents({}) == 20

    for report in json_reports:
        ts = datetime.strptime(report['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
        assert c_output.count_documents(
            {'timestamp': ts, 'sensor': report['sensor'],
             'target': report['target']}) == 2


def test_run_socket_to_mongo(mongo_database, unused_tcp_port, socket_info_config, shutdown_system):
    """
        Check that report are correctly stored into an output mongo database.
        The input source is a socket
    """
    config = socket_info_config
    config['input']['test_puller']['port'] = unused_tcp_port
    supervisor = Supervisor()
    launch_simple_architecture(config=config, supervisor=supervisor, hwpc_depth_level=SOCKET_DEPTH_LEVEL,
                               formula_class=DummyFormulaActor)
    time.sleep(2)
    client = ClientThread(extract_rapl_reports_with_2_sockets(10), unused_tcp_port)
    client.daemon = True
    client.start()

    time.sleep(6)

    check_db_socket()

    supervisor.kill_actors()


def test_run_socket_with_delay_between_message_to_mongo(mongo_database, unused_tcp_port, socket_info_config,
                                                        shutdown_system):
    """
        Check that report are correctly stored into an output mongo database
    """
    config = socket_info_config
    config['input']['test_puller']['port'] = unused_tcp_port
    supervisor = Supervisor()
    launch_simple_architecture(config=config, supervisor=supervisor, hwpc_depth_level=SOCKET_DEPTH_LEVEL,
                               formula_class=DummyFormulaActor)
    time.sleep(5)
    client = ClientThreadDelay(extract_rapl_reports_with_2_sockets(10), unused_tcp_port)
    client.daemon = True
    client.start()

    time.sleep(5)
    check_db_socket()

    supervisor.kill_actors()


##############
# Socket to CSV #
##############
def check_output_file2():
    """
        Check that report are correctly stored into an output file
    """
    input_reports = extract_rapl_reports_with_2_sockets(10)
    output_file = open(OUTPUT_PATH + 'test_sensor-all/PowerReport.csv', 'r')

    # line count
    l_output = -1
    for _ in output_file:
        l_output += 1

    assert len(input_reports) * 2 == l_output
    output_file.seek(0)

    output_file.readline()

    # split socket0 report from socket1 report
    output_socket0 = []
    output_socket1 = []

    for output_line in map(lambda x: x.split(','), output_file):
        if output_line[4] == '\0\n':
            output_socket0.append(output_line)
        else:
            output_socket1.append(output_line)

    # check value
    for report, output_line_s0, output_line_s1 in zip(input_reports, output_socket0, output_socket1):
        ts = datetime.strptime(report['timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
        assert ts == output_line_s0[0]
        assert ts == output_line_s1[0]

        assert report['sensor'] == output_line_s0[1]
        assert report['sensor'] == output_line_s1[1]

        assert report['target'] == output_line_s0[2]
        assert report['target'] == output_line_s1[2]

        assert int(output_line_s0[3]) == 42
        assert int(output_line_s1[3]) == 42


def test_run_socket_to_csv(unused_tcp_port, files, shutdown_system):
    """
        Check that report are correctly stored into an output file.
        The input source is a socket
    """
    config = {'verbose': True,
              'stream': False,
              'output': {'test_pusher': {'type': 'csv',
                                         'tags': 'socket',
                                         'model': 'PowerReport',
                                         'name': 'pusher',
                                         'max_buffer_size': 0,
                                         'directory': OUTPUT_PATH}},
              'input': {'test_puller': {'type': 'socket',
                                        'port': unused_tcp_port,
                                        'model': 'HWPCReport'
                                        }},
              }
    supervisor = Supervisor()
    launch_simple_architecture(config=config, supervisor=supervisor,
                               hwpc_depth_level=SOCKET_DEPTH_LEVEL, formula_class=DummyFormulaActor)

    time.sleep(2)

    client = ClientThread(extract_rapl_reports_with_2_sockets(10), unused_tcp_port)
    client.daemon = True
    client.start()

    time.sleep(4)

    check_output_file2()

    supervisor.kill_actors()
