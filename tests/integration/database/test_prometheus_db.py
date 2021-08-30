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

from powerapi.database import PrometheusDB
from powerapi.report import PowerReport

PORT = 9999
ADDR = 'localhost'
METRIC = 'test'
DESC = 'TEST'
AGG = 1
URL = 'http://' + ADDR + ':' + str(PORT) + '/metrics'

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

    regexp = re.compile(metric_prefix + '_(.*){sensor="(.*)",socket="(.*)",target="(.*)"} (.*)')

    metrics = {}

    for s in filter(lambda s: metric_prefix in s and s[0] != '#', request_result.text.split('\n')):
        [(metric, sensor, socket, target, value)] = re.findall(regexp, s)
        if metric not in metrics:
            metrics[metric] = {}
        if target not in metrics[metric]:
            metrics[metric][target] = []
        metrics[metric][target].append({'socket': socket, 'sensor': sensor, 'value': float(value)})
    return metrics

class Prometheus_server(multiprocessing.Process):
    def __init__(self, q):
        multiprocessing.Process.__init__(self)
        self.q = q

    def run(self):
        db = PrometheusDB(PowerReport, PORT, ADDR, METRIC, DESC, AGG, ['socket'])
        db.connect()
        while True:
            report_list = self.q.get()
            db.save_many(report_list)

@pytest.fixture
def db():
    """
    start a PrometheusDB in a process and return a q to send report to the DB
    """
    q = multiprocessing.Queue()
    p = Prometheus_server(q)
    p.start()
    yield q
    p.terminate()


def test_create_prometheus_db_and_connect_it_must_launch_web_server_on_given_address(db):
    r = requests.get(URL)
    assert r.status_code == 200


def test_create_prometheus_db_and_dont_connect_it_must_not_launch_web_server_on_given_address():
    db = PrometheusDB(PowerReport, PORT, ADDR, METRIC, DESC, AGG, ['socket'])
    with pytest.raises(requests.exceptions.ConnectionError):
        r = requests.get(URL)


def test_save_one_report_must_not_expose_data(db):
    db.put([REPORTA_1])
    assert extract_metrics(METRIC, URL) == {}


def test_save_two_report_with_same_target_must_not_expose_data(db):
    db.put([REPORTA_1, REPORTA_2])
    assert extract_metrics(METRIC, URL) == {}

def test_save_three_report_with_same_target_must_expose_data_for_the_two_first_reports(db):
    db.put([REPORTA_1, REPORTA_2, REPORTA_3])
    assert extract_metrics(METRIC, URL) != {}


def test_save_three_report_with_same_target_must_expose_min_max_mean_and_std_data_for_the_two_first_reports(db):
    db.put([REPORTA_1, REPORTA_2, REPORTA_3])
    data = extract_metrics(METRIC, URL)
    assert 'min' in data
    assert 'max' in data
    assert 'mean' in data
    assert 'std' in data


def test_save_three_report_with_same_target_must_expose_correct_min_max_mean_and_std_data_for_the_two_first_reports(db):
    db.put([REPORTA_1, REPORTA_2, REPORTA_3])
    data = extract_metrics(METRIC, URL)
    assert data['min'][TARGET1][0]['value'] == 10
    assert data['max'][TARGET1][0]['value'] == 20
    assert data['mean'][TARGET1][0]['value'] == 15
    assert data['std'][TARGET1][0]['value'] == 5


def test_save_five_report_with_same_target_must_expose_correct_min_max_mean_and_std_data_for_last_two_report(db):
    db.put([REPORTA_1, REPORTA_2, REPORTA_3, REPORTA_4, REPORTA_5])
    data = extract_metrics(METRIC, URL)
    assert data['min'][TARGET1][0]['value'] == 30
    assert data['max'][TARGET1][0]['value'] == 40
    assert data['mean'][TARGET1][0]['value'] == 35
    assert data['std'][TARGET1][0]['value'] == 5


def test_save_three_report_with_different_target_must_not_expose_data(db):
    db.put([REPORTA_1, REPORTB_2, REPORTA_3])
    assert extract_metrics(METRIC, URL) == {}


def test_save_six_report_with_different_target_must_expose_correct_data_for_each_target(db):
    db.put([REPORTA_1, REPORTB_1, REPORTA_2, REPORTB_2, REPORTA_3, REPORTB_3, ])

    data = extract_metrics(METRIC, URL)
    assert TARGET1 in data['mean']
    assert TARGET2 in data['mean']


def test_save_report_from_two_target_and_then_report_from_one_target_must_finaly_only_expose_report_from_remaining_target(db):
    db.put([REPORTA_1, REPORTB_1, REPORTA_2, REPORTB_2, REPORTA_3, REPORTB_3, REPORTA_4, REPORTA_5, REPORTA_6, REPORTA_7])
    data = extract_metrics(METRIC, URL)
    assert TARGET1 in data['mean']
    assert TARGET2 not in data['mean']
    assert TARGET2 not in data['max']
    assert TARGET1 in data['max']
