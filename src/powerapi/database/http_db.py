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
import random
from threading import Thread
from typing import Type
from wsgiref.simple_server import WSGIServer

from flask import Flask, request
from flask_httpauth import HTTPTokenAuth

from powerapi.database import BaseDB, IterDB
from powerapi.report import Report, HWPCReport

# Constants

DEFAULT_APPLICATION_NAME = 'http_server_source'

CONTENT_TYPE_PROPERTY_NAME = 'Content-Type'

APPLICATION_JSON_TYPE = 'application/json'

DEFAULT_ANSWER = ''

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


@flask_app.post(HWPC_RESOURCE_PATH)
@authentification.login_required
async def process_hwpc_report():
    """
    Process a HWPC Report
    """
    return await store_report(report_type=HWPCReport)


async def store_report(report_type):
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
            await report_queue.put(report)
            return DEFAULT_ANSWER, CREATED_CODE
        else:
            return DEFAULT_ANSWER, BAD_REQUEST_CODE
    else:
        return DEFAULT_ANSWER, BAD_REQUEST_CODE


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

        global flask_app, tokens, report_queue
        tokens = {}
        report_queue = asyncio.Queue()
        self.flask_app = flask_app
        self.tokens = tokens
        self.port = port
        self.host = host
        self.http_server = WSGIServer((host, port), self.flask_app)
        self.report_queue = report_queue

        self.server_thread = None

        if not token:
            token = DEFAULT_TOKEN

        self.tokens[token] = USER_NAME_PREFIX + str(random.randint(USER_NAME_SUFFIX_MIN, USER_NAME_SUFFIX_MAX))

    def connect(self):
        """
        Start an HTTP server receiving the metrics
        """

        def run_wsgi():
            """
            Start the http server
            """
            self.http_server.serve_forever()

        self.server_thread = Thread(target=run_wsgi)
        self.server_thread.start()

    def stop(self):
        """
        Stop the running http server and wait for the end of the thread running it
        """
        self.http_server.shutdown()
        self.server_thread.join(timeout=10)

    def iter(self, stream_mode: bool) -> IterDB:
        global report_queue
        return IterHttpServerDB(report_type=self.report_type, stream_mode=stream_mode, queue=self.report_queue)


class IterHttpServerDB(IterDB):
    """
    iterator connected to a http server that receive reports from a sensor
    """

    def __init__(self, report_type, stream_mode, queue):
        """
        """
        IterDB.__init__(self, None, report_type, stream_mode)

        self.queue = queue

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            report = await asyncio.wait_for(self.queue.get(), 2)
            return report
        except asyncio.TimeoutError:
            return None
