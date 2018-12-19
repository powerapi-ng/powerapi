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
Module smartwatts-cli
"""

import argparse
import pickle
import signal
import zmq
from smartwatts.database import MongoDB
from smartwatts.pusher import PusherActor
from smartwatts.formula import RAPLFormulaActor
from smartwatts.group_by import HWPCGroupBy, HWPCDepthLevel
from smartwatts.filter import HWPCFilter
from smartwatts.puller import PullerActor
from smartwatts.report import HWPCReport, PowerReport
from smartwatts.report_model import HWPCModel
from smartwatts.dispatcher import DispatcherActor
from smartwatts.message import OKMessage, StartMessage


class BadActorInitializationError(Exception):
    """ Error if actor doesn't answer with "OKMessage" """
    pass


def arg_parser_init():
    """ initialize argument parser"""
    parser = argparse.ArgumentParser(
        description="Start SmartWatts with the specified configuration.")

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

    # GroupBy
    parser.add_argument("hwpc_group_by", help="Define the group_by rule, "
                        "Can be CORE, SOCKET or ROOT",
                        choices=['CORE', 'SOCKET', 'ROOT'])

    # Verbosity
    parser.add_argument("-v", "--verbose", help="Enable verbosity",
                        action="store_true", default=False)
    return parser


def main():
    """ Main function """

    ##########################################################################
    # Actor initialization step

    args = arg_parser_init().parse_args()

    # Pusher
    output_mongodb = MongoDB(args.output_hostname, args.output_port,
                             args.output_db, args.output_collection,
                             save_mode=True)
    pusher = PusherActor("pusher_mongodb", PowerReport, output_mongodb,
                         verbose=args.verbose)

    # Formula
    formula_factory = (lambda name, verbose:
                       RAPLFormulaActor(name, pusher, verbose=verbose))

    # Dispatcher
    dispatcher = DispatcherActor('dispatcher', formula_factory,
                                 verbose=args.verbose)
    dispatcher.group_by(HWPCReport, HWPCGroupBy(getattr(HWPCDepthLevel,
                                                        args.hwpc_group_by),
                                                primary=True))

    # Puller
    input_mongodb = MongoDB(args.input_hostname, args.input_port,
                            args.input_db, args.input_collection,
                            report_model=HWPCModel())
    hwpc_filter = HWPCFilter()
    hwpc_filter.filter(lambda msg: True, dispatcher)
    puller = PullerActor("puller_mongodb", input_mongodb,
                         hwpc_filter, 0, verbose=args.verbose)

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

    # start actors
    context = zmq.Context()

    pusher.monitor(context)
    pusher.start()
    dispatcher.monitor(context)
    dispatcher.start()
    puller.monitor(context)
    puller.start()

    # Send StartMessage
    pusher.send_monitor(StartMessage())
    dispatcher.send_monitor(StartMessage())
    puller.send_monitor(StartMessage())

    # Wait for OKMessage
    poller = zmq.Poller()
    poller.register(pusher.state.socket_interface.monitor_socket, zmq.POLLIN)
    poller.register(dispatcher.state.socket_interface.monitor_socket,
                    zmq.POLLIN)
    poller.register(puller.state.socket_interface.monitor_socket, zmq.POLLIN)

    cpt_ok = 0
    while cpt_ok < 3:
        events = poller.poll(100)
        msgs = [pickle.loads(sock.recv()) for sock, event in events
                if event == zmq.POLLIN]
        for msg in msgs:
            if isinstance(msg, OKMessage):
                cpt_ok += 1
            else:
                print("Error message")
                puller.kill()
                puller.join()
                dispatcher.kill()
                dispatcher.join()
                pusher.kill()
                pusher.join()
                exit(0)

    ##########################################################################
    # Actor run step

    # wait
    puller.join()
    dispatcher.kill()
    dispatcher.join()
    pusher.kill()
    pusher.join()

    ##########################################################################


if __name__ == "__main__":
    main()
