# Copyright (c) 2024, INRIA
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

# pylint: disable=W0602

import asyncio
import logging
import random
from multiprocessing import Process, Manager

from typing import Type, List

from waitress import serve

from flask import Flask, request
from flask_httpauth import HTTPTokenAuth

from powerapi.database import BaseDB, IterDB, DBError
from powerapi.report import Report, HWPCReport

# Constants

DEFAULT_APPLICATION_NAME = 'http_server_source'

CONTENT_TYPE_PROPERTY_NAME = 'Content-Type'

APPLICATION_JSON_TYPE = 'application/json'

DEFAULT_ANSWER_STORED_REPORT = 'Report Stored'
DEFAULT_ANSWER_MISSING_REPORT = 'Missing Report'
DEFAULT_ANSWER_BAD_REPORT_TYPE = 'Json expected as Report Type'

DEFAULT_TOKEN = 'default-token'

DEFAULT_PORT = 10000

DEFAULT_HOST = 'localhost'

USER_NAME_PREFIX = "sensor-"

BASE_RESOURCE_PATH = '/api/v1/report/'

HWPC_RESOURCE_PATH = BASE_RESOURCE_PATH + 'HWPCReport'

USER_NAME_SUFFIX_MAX = 2000
USER_NAME_SUFFIX_MIN = 1

CREATED_CODE = 201
BAD_REQUEST_CODE = 400
BAD_REQUEST_CODE = 400
NOT_FOUND_CODE = 404
UNAUTHORIZED_CODE = 401

# Server

flask_app = Flask(import_name=DEFAULT_APPLICATION_NAME)

report_queue = None

# Authentification

authentification = HTTPTokenAuth()

tokens = None


# API

@authentification.verify_token
def verify_token(token):
    """
    Check if authentification is correct when a token is defined. If a token is not defined and the Default token has
    been defined, it means that authentification is disabled
    :return None if the provided token is wrong or a generated value is the token is correct or authentification is
    inactive
    """
    verification_result = None
    if not token and DEFAULT_TOKEN in tokens:
        # This is the case when authentification is not required
        verification_result = tokens[DEFAULT_TOKEN]
    if token in tokens:
        # Authentification is required
        verification_result = tokens[token]
    return verification_result


@flask_app.route("/", methods=['POST', 'GET'])
def hello_world():
    """
    Hello World
    """
    return "Hello, World!"


@flask_app.post(HWPC_RESOURCE_PATH)
@authentification.login_required
def process_hwpc_report():
    """
    Process a HWPC Report
    """
    return store_report(report_type=HWPCReport)


def store_report(report_type):
    """
    Store the provided report in a queue
    :param report_type: The report type related to the report
    """
    content_type = request.headers.get(CONTENT_TYPE_PROPERTY_NAME)

    if content_type == APPLICATION_JSON_TYPE:
        report_json = request.json

        if report_json:
            global report_queue
            report = report_type.from_json(report_json)
            report_queue.put(report)
            return DEFAULT_ANSWER_STORED_REPORT, CREATED_CODE
        else:
            return DEFAULT_ANSWER_MISSING_REPORT, BAD_REQUEST_CODE
    else:
        return DEFAULT_ANSWER_BAD_REPORT_TYPE, BAD_REQUEST_CODE


def get_flask_app():
    """
    Return the flask_app
    """
    global flask_app
    return flask_app


class HttpServerDB(BaseDB):
    """
    Http Server as a source
    """

    def __init__(self, report_type: Type[Report], port: int, host: str, token: str = None):
        BaseDB.__init__(self, report_type)

        # self.asynchrone = False

        global flask_app, tokens, report_queue
        tokens = {}

        self.manager = Manager()
        report_queue = self.manager.Queue(-1)
        self.flask_app = flask_app
        self.tokens = tokens
        self.port = port
        self.host = host
        self.logger = logging.getLogger()
        self.report_queue = report_queue

        self.server_process = None

        if not token:
            token = DEFAULT_TOKEN

        self.tokens[token] = USER_NAME_PREFIX + str(random.randint(USER_NAME_SUFFIX_MIN, USER_NAME_SUFFIX_MAX))

    def connect(self):
        """
        Start an HTTP server receiving the metrics (raw reports)
        """

        def run_wsgi():
            """
            Start the HTPP server
            """
            self.logger.debug('Starting HTTP Server')
            serve(self.flask_app, host=self.host, port=self.port)
            self.logger.debug('HTTP Server stopped')

        self.server_process = Process(target=run_wsgi)

        self.server_process.start()

    def disconnect(self):
        self._stop()

    def _stop(self):
        """
        Stop the running http server and wait for the end of the thread running it
        """
        #
        if self.server_process and self.server_process.is_alive():
            self.server_process.kill()

    def iter(self, stream_mode: bool) -> IterDB:
        global report_queue
        return IterHttpServerDB(report_type=self.report_type, stream_mode=stream_mode, queue=self.report_queue)

    def __iter__(self):
        raise DBError('Http db don\'t support __iter__ method')

    def save(self, report: Report):
        raise DBError('Http db don\'t support save method')

    def save_many(self, reports: List[Report]):
        raise DBError('Http db don\'t support save_many method')


class IterHttpServerDB(IterDB):
    """
    iterator connected to a http server that receive reports from a sensor
    """

    def __init__(self, report_type, stream_mode, queue):
        """
        """
        IterDB.__init__(self, None, report_type, stream_mode)

        self.queue = queue

    def __iter__(self):
        return self

    def __next__(self):
        try:
            report = self.queue.get()
            return report
        except asyncio.TimeoutError:
            return None
