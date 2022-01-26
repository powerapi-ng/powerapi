# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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


import sys

from powerapi.cli.config_parser import MainConfigParser, SubConfigParser
from powerapi.cli.parser import store_true
from powerapi.cli.parser import MissingValueException
from powerapi.cli.parser import BadTypeException, BadContextException
from powerapi.cli.parser import UnknowArgException


def extract_file_names(arg, val, args, acc):
    """
    action used to convert string from --files parameter into a list of file name
    """
    acc[arg] = val.split(",")
    return args, acc


class CommonCLIParser(MainConfigParser):
    """
    PowerAPI basic config parser
    """

    def __init__(self):
        MainConfigParser.__init__(self)

        self.add_argument(
            "v",
            "verbose",
            flag=True,
            action=store_true,
            default=False,
            help="enable verbose mode",
        )
        self.add_argument(
            "s",
            "stream",
            flag=True,
            action=store_true,
            default=False,
            help="enable stream mode",
        )

        subparser_libvirt_mapper_modifier = SubConfigParser("libvirt_mapper")
        subparser_libvirt_mapper_modifier.add_argument(
            "u", "uri", help="libvirt daemon uri", default=""
        )
        subparser_libvirt_mapper_modifier.add_argument(
            "d",
            "domain_regexp",
            help="regexp used to extract domain from cgroup string",
        )
        subparser_libvirt_mapper_modifier.add_argument("n", "name", help="")
        self.add_subparser(
            "report_modifier",
            subparser_libvirt_mapper_modifier,
            help="Specify a report modifier to change input report values : --report_modifier ARG1 ARG2 ...",
        )

        subparser_mongo_input = SubConfigParser("mongodb")
        subparser_mongo_input.add_argument("u", "uri", help="specify MongoDB uri")
        subparser_mongo_input.add_argument(
            "d",
            "db",
            help="specify MongoDB database name",
        )
        subparser_mongo_input.add_argument(
            "c", "collection", help="specify MongoDB database collection"
        )
        subparser_mongo_input.add_argument(
            "n", "name", help="specify puller name", default="puller_mongodb"
        )
        subparser_mongo_input.add_argument(
            "m",
            "model",
            help="specify data type that will be storen in the database",
            default="HWPCReport",
        )
        self.add_subparser(
            "input",
            subparser_mongo_input,
            help="specify a database input : --db_input database_name ARG1 ARG2 ... ",
        )

        subparser_socket_input = SubConfigParser("socket")
        subparser_socket_input.add_argument(
            "p", "port", type=int, help="specify port to bind the socket"
        )
        subparser_socket_input.add_argument(
            "n", "name", help="specify puller name", default="puller_socket"
        )
        subparser_socket_input.add_argument(
            "m",
            "model",
            help="specify data type that will be sent through the socket",
            default="HWPCReport",
        )
        self.add_subparser(
            "input",
            subparser_socket_input,
            help="specify a database input : --db_input database_name ARG1 ARG2 ... ",
        )

        subparser_csv_input = SubConfigParser("csv")
        subparser_csv_input.add_argument(
            "f",
            "files",
            help="specify input csv files with this format : file1,file2,file3",
            action=extract_file_names,
            default=[],
        )
        subparser_csv_input.add_argument(
            "m",
            "model",
            help="specify data type that will be storen in the database",
            default="HWPCReport",
        )
        subparser_csv_input.add_argument(
            "n", "name", help="specify puller name", default="puller_csv"
        )
        self.add_subparser(
            "input",
            subparser_csv_input,
            help="specify a database input : --db_input database_name ARG1 ARG2 ... ",
        )

        subparser_file_input = SubConfigParser("filedb")
        subparser_file_input.add_argument(
            "m",
            "model",
            help="specify data type that will be storen in the database",
            default="PowerReport",
        )
        subparser_file_input.add_argument("f", "filename", help="specify file name")
        subparser_file_input.add_argument(
            "n", "name", help="specify pusher name", default="pusher_filedb"
        )
        self.add_subparser(
            "input",
            subparser_file_input,
            help="specify a database input : --db_input database_name ARG1 ARG2 ... ",
        )

        subparser_file_output = SubConfigParser("filedb")
        subparser_file_output.add_argument(
            "m",
            "model",
            help="specify data type that will be storen in the database",
            default="PowerReport",
        )
        subparser_file_output.add_argument("f", "filename", help="specify file name")
        subparser_file_output.add_argument(
            "n", "name", help="specify pusher name", default="pusher_filedb"
        )
        self.add_subparser(
            "output",
            subparser_file_output,
            help="specify a database output : --db_output database_name ARG1 ARG2 ...",
        )

        subparser_virtiofs_output = SubConfigParser("virtiofs")
        help = "regexp used to extract vm name from report."
        help += "The regexp must match the name of the target in the HWPC-report and a group must"
        subparser_virtiofs_output.add_argument("r", "vm_name_regexp", help=help)
        subparser_virtiofs_output.add_argument(
            "d",
            "root_directory_name",
            help="directory where VM directory will be stored",
        )
        subparser_virtiofs_output.add_argument(
            "p",
            "vm_directory_name_prefix",
            help="first part of the VM directory name",
            default="",
        )
        subparser_virtiofs_output.add_argument(
            "s",
            "vm_directory_name_suffix",
            help="last part of the VM directory name",
            default="",
        )
        subparser_virtiofs_output.add_argument(
            "m",
            "model",
            help="specify data type that will be storen in the database",
            default="PowerReport",
        )
        subparser_virtiofs_output.add_argument(
            "n", "name", help="specify pusher name", default="pusher_virtiofs"
        )
        self.add_subparser(
            "output",
            subparser_virtiofs_output,
            help="specify a database output : --db_output database_name ARG1 ARG2 ...",
        )

        subparser_mongo_output = SubConfigParser("mongodb")
        subparser_mongo_output.add_argument("u", "uri", help="specify MongoDB uri")
        subparser_mongo_output.add_argument(
            "d", "db", help="specify MongoDB database name"
        )
        subparser_mongo_output.add_argument(
            "c", "collection", help="specify MongoDB database collection"
        )

        subparser_mongo_output.add_argument(
            "m",
            "model",
            help="specify data type that will be storen in the database",
            default="PowerReport",
        )
        subparser_mongo_output.add_argument(
            "n", "name", help="specify pusher name", default="pusher_mongodb"
        )
        self.add_subparser(
            "output",
            subparser_mongo_output,
            help="specify a database output : --db_output database_name ARG1 ARG2 ...",
        )

        subparser_prom_output = SubConfigParser("prom")
        subparser_prom_output.add_argument("t", "tags", help="specify report tags")
        subparser_prom_output.add_argument("u", "uri", help="specify server uri")
        subparser_prom_output.add_argument(
            "p", "port", help="specify server port", type=int
        )
        subparser_prom_output.add_argument(
            "M", "metric_name", help="speify metric name"
        )
        subparser_prom_output.add_argument(
            "d",
            "metric_description",
            help="specify metric description",
            default="energy consumption",
        )
        help = "specify number of second for the value must be aggregated before compute statistics on them"
        subparser_prom_output.add_argument(
            "A", "aggregation_period", help=help, default=15, type=int
        )

        subparser_prom_output.add_argument(
            "m",
            "model",
            help="specify data type that will be storen in the database",
            default="PowerReport",
        )
        subparser_prom_output.add_argument(
            "n", "name", help="specify pusher name", default="pusher_prom"
        )
        self.add_subparser(
            "output",
            subparser_prom_output,
            help="specify a database output : --db_output database_name ARG1 ARG2 ...",
        )

        subparser_direct_prom_output = SubConfigParser("direct_prom")
        subparser_direct_prom_output.add_argument(
            "t", "tags", help="specify report tags"
        )
        subparser_direct_prom_output.add_argument("a", "uri", help="specify server uri")
        subparser_direct_prom_output.add_argument(
            "p", "port", help="specify server port", type=int
        )
        subparser_direct_prom_output.add_argument(
            "M", "metric_name", help="speify metric name"
        )
        subparser_direct_prom_output.add_argument(
            "d",
            "metric_description",
            help="specify metric description",
            default="energy consumption",
        )
        subparser_direct_prom_output.add_argument(
            "m",
            "model",
            help="specify data type that will be storen in the database",
            default="PowerReport",
        )
        subparser_direct_prom_output.add_argument(
            "n", "name", help="specify pusher name", default="pusher_prom"
        )
        self.add_subparser(
            "output",
            subparser_direct_prom_output,
            help="specify a database output : --db_output database_name ARG1 ARG2 ...",
        )

        subparser_csv_output = SubConfigParser("csv")
        subparser_csv_output.add_argument(
            "d",
            "directory",
            help="specify directory where where output  csv files will be writen",
        )
        subparser_csv_output.add_argument(
            "m",
            "model",
            help="specify data type that will be storen in the database",
            default="PowerReport",
        )

        subparser_csv_output.add_argument("t", "tags", help="specify report tags")
        subparser_csv_output.add_argument(
            "n", "name", help="specify pusher name", default="pusher_csv"
        )
        self.add_subparser(
            "output",
            subparser_csv_output,
            help="specify a database outpout : --db_output database_name ARG1 ARG2 ... ",
        )

        subparser_influx_output = SubConfigParser("influxdb")
        subparser_influx_output.add_argument("u", "uri", help="specify InfluxDB uri")
        subparser_influx_output.add_argument("t", "tags", help="specify report tags")
        subparser_influx_output.add_argument(
            "d", "db", help="specify InfluxDB database name"
        )
        subparser_influx_output.add_argument(
            "p", "port", help="specify InfluxDB connection port", type=int
        )
        subparser_influx_output.add_argument(
            "m",
            "model",
            help="specify data type that will be storen in the database",
            default="PowerReport",
        )
        subparser_influx_output.add_argument(
            "n", "name", help="specify pusher name", default="pusher_influxdb"
        )
        self.add_subparser(
            "output",
            subparser_influx_output,
            help="specify a database output : --db_output database_name ARG1 ARG2 ... ",
        )

        subparser_opentsdb_output = SubConfigParser("opentsdb")
        subparser_opentsdb_output.add_argument("u", "uri", help="specify openTSDB host")
        subparser_opentsdb_output.add_argument(
            "p", "port", help="specify openTSDB connection port", type=int
        )
        subparser_opentsdb_output.add_argument(
            "metric_name", help="specify metric name"
        )

        subparser_opentsdb_output.add_argument(
            "m",
            "model",
            help="specify data type that will be storen in the database",
            default="PowerReport",
        )
        subparser_opentsdb_output.add_argument(
            "n", "name", help="specify pusher name", default="pusher_opentsdb"
        )
        self.add_subparser(
            "output",
            subparser_opentsdb_output,
            help="specify a database output : --db_output database_name ARG1 ARG2 ... ",
        )

    def parse_argv(self):
        """ """
        try:
            return self.parse(sys.argv[1:])

        except MissingValueException as exn:
            msg = "CLI error : argument " + exn.argument_name + " : expect a value"
            print(msg, file=sys.stderr)

        except BadTypeException as exn:
            msg = "Configuration error : " + exn.msg
            print(msg, file=sys.stderr)

        except UnknowArgException as exn:
            msg = "CLI error : unknow argument " + exn.argument_name
            print(msg, file=sys.stderr)

        except BadContextException as exn:
            msg = "CLI error : argument " + exn.argument_name
            msg += " not used in the correct context\nUse it with the following arguments :"
            for main_arg_name, context_name in exn.context_list:
                msg += "\n  --" + main_arg_name + " " + context_name
            print(msg, file=sys.stderr)

        sys.exit()
