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
from smartwatts.database import MongoDB
from smartwatts.pusher import PusherActor
from smartwatts.formula import RAPLFormulaActor
from smartwatts.group_by import HWPCGroupBy, HWPCDepthLevel
from smartwatts.filter import HWPCFilter
from smartwatts.puller import PullerActor
from smartwatts.report import HWPCReport, PowerReport
from smartwatts.report_model import HWPCModel
from smartwatts.dispatcher import DispatcherActor


class UnknowFormulaError(Exception):
    """ Error if formula doesn't exist """
    pass


def main():
    """ Main function """

    ##########################################################################
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

    # Formula choice
    parser.add_argument("formula", help="Formula you want to use,"
                                        "Can be rapl_formula")

    # GroupBy
    parser.add_argument("hwpc_group_by", help="Define the group_by rule,"
                                              "Can be CORE, SOCKET or ROOT")

    # Timeout
    parser.add_argument("timeout", help="Define the timeout in ms for the "
                                        "puller actor",
                        type=int)

    # Verbosity
    parser.add_argument("-v", "--verbose", help="Enable verbosity",
                        action="store_true")

    args = parser.parse_args()
    ##########################################################################

    ##########################################################################
    # Verbosity
    verbosity = False
    if args.verbose:
        verbosity = True

    # Pusher
    output_mongodb = MongoDB(None, args.output_hostname, args.output_port,
                             args.output_db, args.output_collection,
                             save_mode=True)
    pusher = PusherActor("pusher_mongodb", PowerReport, output_mongodb,
                         verbose=verbosity)

    # Formula
    def gen_factory(formula):
        """ return a factory for the choosing formula """
        if formula == "rapl_formula":
            return (lambda name, verbose:
                    RAPLFormulaActor(name, pusher,
                                     verbose=verbose))

        raise UnknowFormulaError()

    # GroupBy

    # Dispatcher
    dispatcher = DispatcherActor('dispatcher', gen_factory(args.formula),
                                 verbose=verbosity)
    dispatcher.group_by(HWPCReport, HWPCGroupBy(getattr(HWPCDepthLevel,
                                                        args.hwpc_group_by),
                                                primary=True))

    # Puller
    input_mongodb = MongoDB(HWPCModel(), args.input_hostname, args.input_port,
                            args.input_db, args.input_collection)
    hwpc_filter = HWPCFilter()
    hwpc_filter.filter(lambda msg: True, dispatcher)
    puller = PullerActor("puller_mongodb", input_mongodb,
                         hwpc_filter, args.timeout, verbose=verbosity)

    pusher.start()
    dispatcher.start()
    puller.start()
    dispatcher.join()
    pusher.join()
    puller.kill()
    ##########################################################################


if __name__ == "__main__":
    main()
