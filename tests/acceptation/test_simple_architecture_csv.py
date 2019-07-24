"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

"""
Test the behaviour of the most simple architecture using csv files as input and output

Architecture :
  - 1 puller (reading from 3 csv files, stream mode off)
  - 1 dispatcher (HWPC dispatch rule (dispatch by SOCKET)
  - 1 Dummy Formula
  - 1 pusher (writing in one csv file)

csv files contains 4 HWPC reports


Scenario:
  - Launch the full architecture

Test if:
  - each HWPCReport in the intput database was converted in one PowerReport per
    socket in the output database
"""
import os
import logging
import pytest

from powerapi.cli.tools import CommonCLIParser, PusherGenerator, PullerGenerator
from powerapi.backendsupervisor import BackendSupervisor
from powerapi.formula import DummyFormulaActor
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.report import HWPCReport
from powerapi.dispatcher import DispatcherActor, RouteTable


ROOT_PATH = 'tests/unit/environment/csv/'
FILES = [ROOT_PATH + 'core2.csv',
         ROOT_PATH + "rapl2.csv",
         ROOT_PATH + "pcu2.csv"]

LOG_LEVEL = logging.NOTSET


@pytest.fixture
def files():
    os.system('rm -Rf ' + ROOT_PATH + 'grvingt-12-system')
    yield None
    os.system('rm -Rf ' + ROOT_PATH + 'grvingt-12-system')


@pytest.fixture
def supervisor():
    s = BackendSupervisor(False)
    yield s
    s.kill_actors()


def check_output_file():
    input_file = open(ROOT_PATH + 'rapl2.csv', 'r')
    output_file = open(ROOT_PATH + 'grvingt-12-system/PowerReport.csv', 'r')

    # line count
    l_output = 0
    for _ in output_file:
        l_output += 1

    l_input = 0
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
        if output_line[5] == '\'0\')"':
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


def test_run(files, supervisor):

    config = {'verbose': LOG_LEVEL,
              'stream': False,
              'input': {'csv': {'puller' : {'files': FILES,
                                  'model': 'HWPCReport',
                                  'name': 'puller',
                                  }}},
              'output': {'csv': {'pusher': {'model': 'PowerReport', 'name': 'pusher', 'directory': ROOT_PATH}}}}

    # Pusher
    pusher_generator = PusherGenerator()
    pushers = pusher_generator.generate(config)

    # Formula
    formula_factory = (lambda name,
                       verbose: DummyFormulaActor(name, pushers, level_logger=config['verbose']))

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport,
                              HWPCDispatchRule(getattr(HWPCDepthLevel, 'SOCKET'), primary=True))

    dispatcher = DispatcherActor('dispatcher', formula_factory, route_table,
                                 level_logger=LOG_LEVEL)

    # Puller
    report_filter = Filter()
    report_filter.filter(lambda msg: True, dispatcher)
    puller_generator = PullerGenerator(report_filter)
    pullers = puller_generator.generate(config)

    for _, pusher in pushers.items():
        supervisor.launch_actor(pusher)

    supervisor.launch_actor(dispatcher)

    for _, puller in pullers.items():
        supervisor.launch_actor(puller)

    supervisor.join()

    check_output_file()
