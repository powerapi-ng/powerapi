# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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
import re
import multiprocessing
import datetime
import time

import requests
import pytest

from powerapi.database import DirectPrometheusDB
from powerapi.report import PowerReport
from powerapi.test_utils.abstract_test import recv_from_pipe

ADDR = 'localhost'
METRIC = 'test'
DESC = 'TEST'

TARGET1 = 'targetA'
TARGET2 = 'targetB'

REPORTA_1 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 0), 0, TARGET1, 10, {'socket': 0})
REPORTA_2 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 1), 0, TARGET1, 20, {'socket': 0})
REPORTA_3 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 2), 0, TARGET1, 30, {'socket': 0})
REPORTA_4 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 3), 0, TARGET1, 40, {'socket': 0})
REPORTA_5 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 4), 0, TARGET1, 50, {'socket': 0})
REPORTA_6 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 5), 0, TARGET1, 60, {'socket': 0})
REPORTA_7 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 6), 0, TARGET1, 70, {'socket': 0})

REPORTB_1 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 0), 0, TARGET2, 40, {'socket': 0})
REPORTB_2 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 1), 0, TARGET2, 60, {'socket': 0})
REPORTB_3 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 2), 0, TARGET2, 70, {'socket': 0})
REPORTB_4 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 3), 0, TARGET2, 80, {'socket': 0})
REPORTB_5 = PowerReport(datetime.datetime(1970, 1, 1, 1, 1, 4), 0, TARGET2, 90, {'socket': 0})

def extract_metrics(metric_prefix, url):
    time.sleep(0.5)
    request_result = requests.get(url)
    regexp = re.compile(metric_prefix + '{sensor="(.*)",socket="(.*)",target="(.*)"} (.*)')

    metrics = {}

    for s in filter(lambda s: metric_prefix in s and s[0] != '#', request_result.text.split('\n')):
        [(sensor, socket, target, value)] = re.findall(regexp, s)
        if target not in metrics:
            metrics[target] = []
        metrics[target].append({'socket': socket, 'sensor': sensor, 'value': float(value)})
    return metrics

class DirectPrometheusServer(multiprocessing.Process):
    def __init__(self, q, port):
        multiprocessing.Process.__init__(self)
        self.port = port
        self.q = q

    def run(self):
        db = DirectPrometheusDB(PowerReport, self.port, ADDR, METRIC, DESC, ['socket'])
        db.connect()
        self.q.put('ok')
        while True:
            report_list = self.q.get()
            db.save_many(report_list)


def _gen_serv(unused_tcp_port_factory):
    port = unused_tcp_port_factory()
    q = multiprocessing.Queue()
    p = DirectPrometheusServer(q, port)
    p.start()
    return port, q, p


@pytest.fixture
def db_info(unused_tcp_port_factory):
    """
    start a DirectPrometheusDB in a process and return a q to send report to the DB
    """
    port, q, p = _gen_serv(unused_tcp_port_factory)
    if q.get(timeout=1) == 'ok':
        yield q, _gen_url(port)
    else:
        p.terminate()
        port, q, p = _gen_serv(unused_tcp_port_factory)
        yield q, _gen_url(port)
    p.terminate()

def _gen_url(port):
    return 'http://' + ADDR + ':' + str(port) + '/metrics'


def test_create_direct_prometheus_db_and_connect_it_must_launch_web_server_on_given_address(db_info):
    db, url = db_info
    r = requests.get(url)
    assert r.status_code == 200


def test_create_direct_prometheus_db_and_dont_connect_it_must_not_launch_web_server_on_given_address(unused_tcp_port):
    db = DirectPrometheusDB(PowerReport, unused_tcp_port, ADDR, METRIC, DESC, ['socket'])
    with pytest.raises(requests.exceptions.ConnectionError):
        r = requests.get(_gen_url(unused_tcp_port))


def test_save_one_report_must_expose_data(db_info):
    db, url = db_info
    db.put([REPORTA_1])
    assert extract_metrics(METRIC, url) != {}


def test_save_one_report_must_expose_energy_metric_for_the_given_target(db_info):
    db, url = db_info
    db.put([REPORTA_1])
    data = extract_metrics(METRIC, url)
    assert TARGET1 in data


def test_save_one_report_must_expose_correct_value(db_info):
    db, url = db_info
    db.put([REPORTA_1])
    data = extract_metrics(METRIC, url)
    assert data[TARGET1][0]['value'] == 10


def test_save_two_reports_with_same_target_must_expose_correct_energy_value_for_second_report(db_info):
    db, url = db_info
    db.put([REPORTA_1, REPORTA_2])
    data = extract_metrics(METRIC, url)
    assert data[TARGET1][0]['value'] == 20


def test_save_two_report_with_different_target_must_expose_data_for_the_two_target(db_info):
    db, url = db_info
    db.put([REPORTA_1, REPORTB_1])
    data = extract_metrics(METRIC, url)
    assert TARGET1 in data
    assert TARGET2 in data


def test_save_two_report_with_different_target_must_expose_correct_data_for_each_target(db_info):
    db, url = db_info
    db.put([REPORTA_1, REPORTB_1])

    data = extract_metrics(METRIC, url)
    assert data[TARGET1][0]['value'] == 10
    assert data[TARGET2][0]['value'] == 40


def test_save_report_from_two_target_and_then_report_from_one_target_must_finaly_only_expose_report_from_remaining_target(db_info):
    db, url = db_info
    db.put([REPORTA_1, REPORTB_1, REPORTA_2, REPORTA_3])
    data = extract_metrics(METRIC, url)
    assert TARGET1 in data
    assert TARGET2 not in data
