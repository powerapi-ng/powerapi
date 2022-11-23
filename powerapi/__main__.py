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

import logging
import signal
import sys
import json
from typing import Dict

from powerapi import __version__ as powerapi_version
from powerapi.dispatcher import RouteTable

from powerapi.cli import ConfigValidator
from powerapi.cli.tools import store_true, CommonCLIParser
from powerapi.cli.generator import ReportModifierGenerator, PullerGenerator, PusherGenerator
from powerapi.message import DispatcherStartMessage
from powerapi.report import HWPCReport
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.actor import InitializationException
from powerapi.supervisor import Supervisor


from rapl_formula import __version__ as rapl_formula_version
from rapl_formula.dispatcher import RAPLDispatcherActor
from rapl_formula.actor import RAPLFormulaActor, RAPLValues
from rapl_formula.context import RAPLFormulaScope, RAPLFormulaConfig


def generate_rapl_parser():
    """
    Construct and returns the SmartWatts cli parameters parser.
    :return: SmartWatts cli parameters parser
    """
    parser = CommonCLIParser()

    # Formula control parameters
    parser.add_argument('enable-cpu-formula', help='Enable CPU formula', flag=True, type=bool, default=True, action=store_true)
    parser.add_argument('enable-dram-formula', help='Enable DRAM formula', flag=True, type=bool, default=True, action=store_true)

    # Formula RAPL reference event
    parser.add_argument('cpu-rapl-ref-event', help='RAPL event used as reference for the CPU power models', default='RAPL_ENERGY_PKG')
    parser.add_argument('dram-rapl-ref-event', help='RAPL event used as reference for the DRAM power models', default='RAPL_ENERGY_DRAM')

    # Sensor information
    parser.add_argument('sensor-report-sampling-interval', help='The frequency with which measurements are made (in milliseconds)', type=int, default=1000)

    return parser


def filter_rule(_):
    """
    Rule of filter. Here none
    """
    return True


def setup_cpu_formula_actor(supervisor, fconf, route_table, report_filter, power_pushers):
    """
    Setup CPU formula actor.
    :param supervisor: Actor supervisor
    :param fconf: Global configuration
    :param route_table: Reports routing table
    :param report_filter: Reports filter
    :param pushers: Reports pushers
    """

    formula_config = RAPLFormulaConfig(RAPLFormulaScope.CPU, fconf['sensor-report-sampling-interval'],
                                       fconf['cpu-rapl-ref-event'])

    dispatcher_start_message = DispatcherStartMessage('system', 'cpu_dispatcher', RAPLFormulaActor,
                                                      RAPLValues(power_pushers, formula_config),
                                                      route_table, 'cpu')
    cpu_dispatcher = supervisor.launch(RAPLDispatcherActor, dispatcher_start_message)
    report_filter.filter(filter_rule, cpu_dispatcher)


def setup_dram_formula_actor(supervisor, fconf, route_table, report_filter, power_pushers):
    """
    Setup DRAM formula actor.
    :param supervisor: Actor supervisor
    :param fconf: Global configuration
    :param route_table: Reports routing table
    :param report_filter: Reports filter
    :param pushers: Reports pushers
    :return: Initialized DRAM dispatcher actor
    """
    formula_config = RAPLFormulaConfig(RAPLFormulaScope.DRAM,
                                       fconf['sensor-report-sampling-interval'],
                                       fconf['dram-rapl-ref-event'])

    dispatcher_start_message = DispatcherStartMessage('system',
                                                      'dram_dispatcher',
                                                      RAPLFormulaActor,
                                                      RAPLValues(power_pushers, formula_config),
                                                      route_table, 'dram')
    dram_dispatcher = supervisor.launch(RAPLDispatcherActor, dispatcher_start_message)
    report_filter.filter(filter_rule, dram_dispatcher)


def run_rapl(args) -> None:
    """
    Run PowerAPI with the SmartWatts formula.
    :param args: CLI arguments namespace
    :param logger: Logger to use for the actors
    """
    fconf = args

    logging.info('RAPL-Formula version %s using PowerAPI version %s', rapl_formula_version, powerapi_version)

    if not fconf['enable-cpu-formula'] and not fconf['enable-dram-formula']:
        logging.error('You need to enable at least one formula')
        return

    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(HWPCDepthLevel.SOCKET, primary=True))

    report_filter = Filter()

    report_modifier_list = ReportModifierGenerator().generate(fconf)

    supervisor = Supervisor(args['verbose'])

    def term_handler(_, __):
        supervisor.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, term_handler)
    signal.signal(signal.SIGINT, term_handler)
    try:
        logging.info('Starting RAPL-formula actors...')

        power_pushers = {}
        pushers_info = PusherGenerator().generate(args)
        for pusher_name in pushers_info:
            pusher_cls, pusher_start_message = pushers_info[pusher_name]
            power_pushers[pusher_name] = supervisor.launch(
                pusher_cls, pusher_start_message
            )

        logging.info('CPU formula is %s' % ('DISABLED' if not fconf['enable-cpu-formula'] else 'ENABLED'))
        if fconf['enable-cpu-formula']:
            logging.info('CPU formula parameters: RAPL_REF=%s' % (fconf['cpu-rapl-ref-event']))
            setup_cpu_formula_actor(supervisor, fconf, route_table, report_filter, power_pushers)

            logging.info('DRAM formula is %s' % ('DISABLED' if not fconf['enable-dram-formula'] else 'ENABLED'))
        if fconf['enable-dram-formula']:
            logging.info('DRAM formula parameters: RAPL_REF=%s' % (fconf['dram-rapl-ref-event']))
            setup_dram_formula_actor(supervisor, fconf, route_table, report_filter, power_pushers)

        pullers_info = PullerGenerator(report_filter, report_modifier_list).generate(args)
        for puller_name in pullers_info:
            puller_cls, puller_start_message = pullers_info[puller_name]
            supervisor.launch(puller_cls, puller_start_message)
    except InitializationException as exn:
        logging.error('Actor initialization error: ' + exn.msg)
        supervisor.shutdown()
        sys.exit(-1)

    logging.info('RAPL-formula is now running...')
    supervisor.monitor()
    logging.info('RAPL-formula is shutting down...')


def get_config_file(argv):
    """
    Get config file from argv
    """
    i = 0
    for s in argv:
        if s == '--config-file':
            if i + 1 == len(argv):
                logging.error("config file path needed with argument --config-file")
                sys.exit(-1)
            return argv[i + 1]
        i += 1
    return None


def get_config_from_file(file_path):
    """
    Get the config from the config file
    """
    config_file = open(file_path, 'r')
    return json.load(config_file)


class RAPLConfigValidator(ConfigValidator):
    """
    Class used that check the config extracted and verify it conforms to constraints
    """
    @staticmethod
    def validate(config: Dict):
        if not ConfigValidator.validate(config):
            return False

        if 'enable-cpu-formula' not in config:
            config['enable-cpu-formula'] = False
        if 'enable-dram-formula' not in config:
            config['enable-dram-formula'] = False
        if 'cpu-rapl-ref-event' not in config:
            config['cpu-rapl-ref-event'] = 'RAPL_ENERGY_PKG'
        if 'dram-rapl-ref-event' not in config:
            config['dram-rapl-ref-event'] = 'RAPL_ENERGY_DRAM'
        if 'cpu-tdp' not in config:
            config['cpu-tdp'] = 125
        if 'cpu-base-clock' not in config:
            config['cpu-base-clock'] = 100
        if 'sensor-report-sampling-interval' not in config:
            config['sensor-report-sampling-interval'] = 1000
        return True


def get_config():
    """
    Get he config from the cli args
    """
    parser = generate_rapl_parser()
    return parser.parse()


if __name__ == "__main__":
    conf = get_config()
    if not RAPLConfigValidator.validate(conf):
        sys.exit(-1)
    logging.basicConfig(level=logging.WARNING if conf['verbose'] else logging.INFO)
    logging.captureWarnings(True)

    logging.debug(str(conf))
    run_rapl(conf)
    sys.exit(0)
