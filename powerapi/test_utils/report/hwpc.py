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
import json
from typing import Dict

from powerapi.report import HWPCReport, create_socket_report, create_report_root, create_group_report, create_core_report
import powerapi.test_utils.report as parent_module
from powerapi.report_model import HWPCModel


###################
# Report Creation #
###################
def extract_rapl_reports_with_2_sockets(number_of_reports: int) -> Dict:
    """
    Extract the number_of_reports first reports of the file hwpc_rapl_2_socket.json
    This file contain hwpc reports with only RAPL_PKG events, recorded on a two socket host
    """
    path = parent_module.__path__[0]
    json_file = open(path + '/hwpc_rapl_2_socket.json', 'r')
    reports = json.load(json_file)
    json_file.close()
    return reports['reports'][:number_of_reports]

def extract_reports(n):
    # todo: a dégager
    path = parent_module.__path__[0]
    json_file = open(path + '/hwpc.json', 'r')
    reports = list(map(HWPCReport.deserialize, json.load(json_file)['reports']))
    
    json_file.close()
    return reports[:n]


def gen_hwpc_report():
    # todo: a dégager
    """
    Return a well formated HWPCReport
    """
    cpua = create_core_report('1', 'e0', '0')
    cpub = create_core_report('2', 'e0', '1')
    cpuc = create_core_report('1', 'e0', '2')
    cpud = create_core_report('2', 'e0', '3')
    cpue = create_core_report('1', 'ne1', '0')
    cpuf = create_core_report('2', 'e1', '1')
    cpug = create_core_report('1', 'e1', '2')
    cpuh = create_core_report('2', 'e1', '3')

    socketa = create_socket_report('1', [cpua, cpub])
    socketb = create_socket_report('2', [cpuc, cpud])
    socketc = create_socket_report('1', [cpue, cpuf])
    socketd = create_socket_report('2', [cpug, cpuh])

    groupa = create_group_report('1', [socketa, socketb])
    groupb = create_group_report('2', [socketc, socketd])

    return create_report_root([groupa, groupb])
