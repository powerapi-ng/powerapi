# Copyright (c) 2024, Inria
# Copyright (c) 2024, University of Lille
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

import socket as sock
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest
from werkzeug.datastructures import Authorization

from powerapi.database.http_db import HttpServerDB, CREATED_CODE, NOT_FOUND_CODE, UNAUTHORIZED_CODE, HWPC_RESOURCE_PATH
from powerapi.report import HWPCReport

REPORT_TYPE = HWPCReport
LOCALHOST = 'localhost'
WRONG_HOST_1 = '196.54.56.4'
WRONG_HOST_2 = '0.0.0.1'

ALL_PUBLIC_IPS = '0.0.0.0'

PORT = 10000
OPEN_PORT_STATE = 0

NUMBER_OF_REPORTS_FOR_TESTING = 50


@pytest.mark.parametrize('number_of_reports_to_extract, host_token_port',
                         [(NUMBER_OF_REPORTS_FOR_TESTING, (LOCALHOST, None, PORT))])
def test_process_hwpc_report_without_authentification_works_with_correct_uri(hwpc_reports, started_server,
                                                                             rest_client):
    """
    Test that the processing with authentification disabled (token = None) is working when using a correct uri
    """
    for report_number in range(0, NUMBER_OF_REPORTS_FOR_TESTING):
        response = rest_client.post(HWPC_RESOURCE_PATH, json=hwpc_reports[report_number])
        assert response.status_code == CREATED_CODE

    assert started_server.report_queue.qsize() == NUMBER_OF_REPORTS_FOR_TESTING


@pytest.mark.parametrize('number_of_reports_to_extract, host_token_port',
                         [(NUMBER_OF_REPORTS_FOR_TESTING, (LOCALHOST, None, PORT))])
def test_process_hwpc_report_without_authentification_fails_with_wrong_resource_uri(hwpc_reports,
                                                                                    started_server, rest_client):
    """
    Test that the processing with authentification disabled (token = None) fails when a wrong uri is used
    """
    for report_number in range(0, NUMBER_OF_REPORTS_FOR_TESTING):
        response = rest_client.post('/api/v1/report/PowerReport', json=hwpc_reports[report_number])
        assert response.status_code == NOT_FOUND_CODE

    assert started_server.report_queue.qsize() == 0


@pytest.mark.parametrize('number_of_reports_to_extract, host_token_port',
                         [(NUMBER_OF_REPORTS_FOR_TESTING, (LOCALHOST, 'my_token', PORT))])
def test_process_hwpc_report_with_authentification_works_with_login(host_token_port, hwpc_reports, started_server,
                                                                    rest_client):
    """
    Test that the processing with authentification enable (token != None) is working when using a correct token
    """
    for report_number in range(0, NUMBER_OF_REPORTS_FOR_TESTING):
        response = rest_client.post(HWPC_RESOURCE_PATH, json=hwpc_reports[report_number],
                                    auth=Authorization(token=host_token_port[1], auth_type='Bearer'))
        assert response.status_code == CREATED_CODE

    assert started_server.report_queue.qsize() == NUMBER_OF_REPORTS_FOR_TESTING


@pytest.mark.parametrize('number_of_reports_to_extract, host_token_port',
                         [(NUMBER_OF_REPORTS_FOR_TESTING, (LOCALHOST, 'my_token', PORT))])
def test_process_hwpc_report_with_authentification_fails_without_login(hwpc_reports, started_server, rest_client):
    """
    Test that the processing with authentification enable (token != None) fails when no token is provided
    """
    for report_number in range(0, NUMBER_OF_REPORTS_FOR_TESTING):
        response = rest_client.post(HWPC_RESOURCE_PATH, json=hwpc_reports[report_number])
        assert response.status_code == UNAUTHORIZED_CODE

    assert started_server.report_queue.qsize() == 0


@pytest.mark.parametrize('number_of_reports_to_extract, host_token_port',
                         [(NUMBER_OF_REPORTS_FOR_TESTING, (LOCALHOST, 'my_token', PORT))])
def test_process_hwpc_report_with_authentification_fails_with_wrong_login(hwpc_reports, started_server,
                                                                          rest_client):
    """
    Test that the processing with authentification enable (token != None) fails when using a wrong token
    """
    for report_number in range(0, NUMBER_OF_REPORTS_FOR_TESTING):
        response = rest_client.post(HWPC_RESOURCE_PATH, json=hwpc_reports[report_number],
                                    auth=Authorization(token='wrong_token', auth_type='Bearer'))
        assert response.status_code == UNAUTHORIZED_CODE

    assert started_server.report_queue.qsize() == 0
