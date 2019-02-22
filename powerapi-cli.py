# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Module powerapi-cli
"""

import argparse
import logging
import signal
import zmq
from powerapi.actor import ActorInitError, Supervisor
from powerapi.database import MongoDB
from powerapi.pusher import PusherActor
from powerapi.formula import RAPLFormulaActor
from powerapi.dispatch_rule import HWPCDispatchRule, HWPCDepthLevel
from powerapi.filter import Filter
from powerapi.puller import PullerActor
from powerapi.report import HWPCReport, PowerReport
from powerapi.report_model import HWPCModel
from powerapi.dispatcher import DispatcherActor, RouteTable


class BadActorInitializationError(Exception):
    """ Error if actor doesn't answer with "OKMessage" """


def arg_parser_init():
    """ initialize argument parser"""
    parser = argparse.ArgumentParser(
        description="Start PowerAPI with the specified configuration.")

    # MongoDB input
    parser.add_argument("input_hostname", help="MongoDB input hostname")
    parser.add_argument("input_port", help="MongoDB input port", type=int)
    parser.add_argument("input_db", help="MongoDB input database")
    parser.add_argument("input_collection", help="MongoDB input collection")

    # MongoDB output
    parser.add_argument("output_hostname", help="MongoDB output hostname")
    parser.add_argument("output_port", help="MongoDB output port", type=int)
    parser.add_argument("output_db", help="MongoDB output database")
    parser.add_argument("output_collection", help="MongoDB output collection")

    # DispatchRule
    parser.add_argument("hwpc_dispatch_rule", help=
                        "Define the dispatch_rule rule, "
                        "Can be CORE, SOCKET or ROOT",
                        choices=['CORE', 'SOCKET', 'ROOT'])

    # Verbosity
    parser.add_argument("-v", "--verbose", help="Enable verbosity",
                        action="store_true", default=False)
    return parser


def launch_powerapi(args, logger):
    ##########################################################################
    # Actor Creation

    # Pusher
    output_mongodb = MongoDB(args.output_hostname, args.output_port,
                             args.output_db, args.output_collection,
                             HWPCModel())
    pusher = PusherActor("pusher_mongodb", PowerReport, output_mongodb,
                         level_logger=args.verbose)

    # Formula
    formula_factory = (lambda name, verbose:
                       RAPLFormulaActor(name, pusher, level_logger=verbose))

    # Dispatcher
    route_table = RouteTable()
    route_table.dispatch_rule(HWPCReport, HWPCDispatchRule(
        getattr(HWPCDepthLevel, args.hwpc_dispatch_rule), primary=True))

    dispatcher = DispatcherActor('dispatcher', formula_factory, route_table,
                                 level_logger=args.verbose)

    # Puller
    input_mongodb = MongoDB(args.input_hostname, args.input_port,
                            args.input_db, args.input_collection,
                            HWPCModel())
    report_filter = Filter()
    report_filter.filter(lambda msg: True, dispatcher)
    puller = PullerActor("puller_mongodb", input_mongodb,
                         report_filter, level_logger=args.verbose)

    ##########################################################################
    # Actor start step

    # Setup signal handler
    def term_handler(_, __):
        puller.join()
        dispatcher.join()
        pusher.join()
        exit(0)

    signal.signal(signal.SIGTERM, term_handler)
    signal.signal(signal.SIGINT, term_handler)

    supervisor = Supervisor()
    try:
        supervisor.launch_actor(pusher)
        supervisor.launch_actor(dispatcher)
        supervisor.launch_actor(puller)

    except zmq.error.ZMQError as exn:
        logger.error('Communication error, ZMQError code : ' + str(exn.errno) +
                     ' reason : ' + exn.strerror)
        supervisor.kill_actors()
    except ActorInitError as exn:
        logger.error('Actor initialisation error, reason : ' + exn.message)
        supervisor.kill_actors()

    ##########################################################################
    # Actor run step

    # wait
    supervisor.join()

    ##########################################################################


if __name__ == "__main__":
    ARGS = arg_parser_init().parse_args()
    if ARGS.verbose:
        ARGS.verbose = logging.DEBUG

    LOGGER = logging.getLogger('main_logger')
    LOGGER.setLevel(ARGS.verbose)
    LOGGER.addHandler(logging.StreamHandler())
    launch_powerapi(ARGS, LOGGER)
