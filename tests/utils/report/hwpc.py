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

import json

import tests.utils.report as parent_module
from powerapi.report import HWPCReport


def extract_rapl_reports_with_2_sockets(number_of_reports: int) -> list[dict]:
    """
    Extract the number_of_reports first reports of the file hwpc_rapl_2_socket.json
    This file contain hwpc reports with only RAPL_PKG events, recorded on a two socket host
    :return: a list of reports. Each reports is a json dictionary
    """
    path = parent_module.__path__[0]
    with open(f'{path}/hwpc_rapl_2_socket.json', 'r', encoding='utf-8') as json_file:
        reports = json.load(json_file)
        return reports['reports'][:number_of_reports]


def extract_all_events_reports_with_2_sockets(number_of_reports: int) -> list[dict]:
    """
    Extract the number_of_reports first reports of the file hwpc_rapl_2_socket.json
    This file contain hwpc reports , recorded on a two socket host, with events :
    - RAPL_PKG
    - MPERF
    - APERF
    - TSC
    - CPU_CLK_THREAD_UNHALTED:THREAD_P
    - CPU_CLK_THREAD_UNHALTED:REF_P
    - LLC_MISSES
    - INSTRUCTIONS_RETIRED
    :return: a list of reports. Each reports is a json dictionary
    """
    path = parent_module.__path__[0]
    with open(f'{path}/hwpc_all_events_2_socket.json', 'r', encoding='utf-8') as json_file:
        reports = json.load(json_file)
        return reports['reports'][:number_of_reports]


def gen_HWPCReports(number_of_reports: int) -> list[HWPCReport]:
    """
    generate number_of_reports HWPCReport extracted from the file hwpc.json
    :return: a list of HWPCReport
    """
    path = parent_module.__path__[0]
    with open(f'{path}/hwpc.json', 'r', encoding='utf-8') as json_file:
        reports = list(map(HWPCReport.from_json, json.load(json_file)['reports']))
        return reports[:number_of_reports]
