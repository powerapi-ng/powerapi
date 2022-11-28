# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille

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
from typing import Dict, Literal

from powerapi import __version__ as powerapi_version
from powerapi.backend_supervisor import BackendSupervisor
from powerapi.dispatcher import RouteTable, DispatcherActor

from powerapi.cli import ConfigValidator
from powerapi.cli.tools import store_true, CommonCLIParser
from powerapi.cli.generator import ReportModifierGenerator, PullerGenerator, PusherGenerator
from powerapi.dispatcher.rapl.rapl_dispatcher_actor import RAPLDispatcherActor
from powerapi.report import HWPCReport
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.actor import InitializationException, Supervisor

from powerapi import __version__ as rapl_formula_version
from powerapi.formula.rapl.rapl_formula_actor import RAPLFormulaActor, RAPLFormulaScope, RAPLFormulaConfig


def generate_rapl_parser():
    """
    Construct and returns the SmartWatts cli parameters parser.
    :return: SmartWatts cli parameters parser
    """
    parser = CommonCLIParser()

    # Formula control parameters
    parser.add_argument('enable-cpu-formula', help='Enable CPU formula', flag=True, type=bool, default=True,
                        action=store_true)
    parser.add_argument('enable-dram-formula', help='Enable DRAM formula', flag=True, type=bool, default=True,
                        action=store_true)

    # Formula RAPL reference event
    parser.add_argument('cpu-rapl-ref-event', help='RAPL event used as reference for the CPU power models',
                        default='RAPL_ENERGY_PKG')
    parser.add_argument('dram-rapl-ref-event', help='RAPL event used as reference for the DRAM power models',
                        default='RAPL_ENERGY_DRAM')

    # Sensor information
    parser.add_argument('sensor-report-sampling-interval',
                        help='The frequency with which measurements are made (in milliseconds)', type=int, default=1000)

    return parser


def filter_rule(_):
    """
    Rule of filter. Here none
    """
    return True


def setup_cpu_formula_actor(supervisor: Supervisor, fconf: Dict, route_table: RouteTable, report_filter: Filter,
                            power_pushers: Dict, logger_level: Literal = logging.INFO):
    """
    Setup CPU formula actor.
    :param supervisor: Actor supervisor
    :param fconf: Global configuration
    :param route_table: Reports routing table
    :param report_filter: Reports filter
    :param power_pushers: Reports pushers
    :param logger_level: Logger level
    """

    formula_config = RAPLFormulaConfig(scope=RAPLFormulaScope.CPU,
                                       reports_frequency=fconf['sensor-report-sampling-interval'],
                                       rapl_event=fconf['cpu-rapl-ref-event'])

    cpu_dispatcher = RAPLDispatcherActor(name='cpu_dispatcher',
                                         formula_init_function=RAPLFormulaActor,
                                         route_table=route_table,
                                         pushers=power_pushers,
                                         level_logger=logger_level,
                                         device_id='cpu',
                                         formula_config=formula_config)

    supervisor.launch_actor(cpu_dispatcher)

    report_filter.filter(filter_rule, cpu_dispatcher)


def setup_dram_formula_actor(supervisor: Supervisor, fconf: Dict, route_table: RouteTable, report_filter: Filter,
                             power_pushers: Dict, logger_level: Literal = logging.INFO):
    """
    Setup DRAM formula actor.
    :param supervisor: Actor supervisor
    :param fconf: Global configuration
    :param route_table: Reports routing table
    :param report_filter: Reports filter
    :param power_pushers: Reports pushers
    :param logger_level: Logger level
    :return: Initialized DRAM dispatcher actor
    """
    formula_config = RAPLFormulaConfig(scope=RAPLFormulaScope.DRAM,
                                       reports_frequency=fconf['sensor-report-sampling-interval'],
                                       rapl_event=fconf['dram-rapl-ref-event'])

    dram_dispatcher = RAPLDispatcherActor(name='dram_dispatcher',
                                          formula_init_function=RAPLFormulaActor,
                                          route_table=route_table,
                                          pushers=power_pushers,
                                          level_logger=logger_level,
                                          device_id='dram',
                                          formula_config=formula_config)

    supervisor.launch_actor(dram_dispatcher)
    report_filter.filter(filter_rule, dram_dispatcher)


def run_rapl(fconf) -> None:
    """
    Run PowerAPI with the RAPL formula.
    :param fconf: CLI arguments namespace
    """

    verbose = fconf['verbose']
    logger_level = logging.INFO

    if verbose:
        logger_level = logging.WARNING

    logging.info('RAPL-Formula version %s using PowerAPI version %s', rapl_formula_version, powerapi_version)

    if not fconf['enable-cpu-formula'] and not fconf['enable-dram-formula']:
        logging.error('You need to enable at least one formula')
        return

    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(HWPCDepthLevel.SOCKET, primary=True))

    report_filter = Filter()

    report_modifier_list = ReportModifierGenerator().generate(fconf)

    supervisor = BackendSupervisor(fconf['stream'])

    def term_handler(_, __):
        supervisor.kill_actors()
        sys.exit(0)

    signal.signal(signal.SIGTERM, term_handler)
    signal.signal(signal.SIGINT, term_handler)
    try:
        logging.info('Starting RAPL-formula actors...')

        power_pushers = {}
        pushers_info = PusherGenerator().generate(fconf)
        for pusher_name in pushers_info:
            pusher = pushers_info[pusher_name]
            power_pushers[pusher_name] = pusher
            supervisor.launch_actor(pusher)

        logging.info('CPU formula is %s' % ('DISABLED' if not fconf['enable-cpu-formula'] else 'ENABLED'))
        if fconf['enable-cpu-formula']:
            logging.info('CPU formula parameters: RAPL_REF=%s' % (fconf['cpu-rapl-ref-event']))
            setup_cpu_formula_actor(supervisor=supervisor, fconf=fconf, route_table=route_table,
                                    report_filter=report_filter, power_pushers=power_pushers, logger_level=logger_level)

            logging.info('DRAM formula is %s' % ('DISABLED' if not fconf['enable-dram-formula'] else 'ENABLED'))
        if fconf['enable-dram-formula']:
            logging.info('DRAM formula parameters: RAPL_REF=%s' % (fconf['dram-rapl-ref-event']))
            setup_dram_formula_actor(supervisor=supervisor, fconf=fconf, route_table=route_table,
                                     report_filter=report_filter, power_pushers=power_pushers,
                                     logger_level=logger_level)

        pullers_info = PullerGenerator(report_filter, report_modifier_list).generate(fconf)
        for puller_name in pullers_info:
            puller = pullers_info[puller_name]
            supervisor.launch_actor(puller)
    except InitializationException as exn:
        logging.error('Actor initialization error: ' + exn.msg)
        supervisor.kill_actors()
        sys.exit(-1)

    logging.info('RAPL-formula is now running...')
    supervisor.join()
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
    logging.basicConfig(level=logging.WARNING if conf['verbose'] else logging.INFO,
                        handlers=[logging.StreamHandler(sys.stdout)])
    logging.captureWarnings(True)

    logging.debug(str(conf))
    run_rapl(conf)
    sys.exit(0)
