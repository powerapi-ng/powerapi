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

import sys

from powerapi.cli.parsing_manager import RootConfigParsingManager, SubgroupConfigParsingManager
from powerapi.cli.config_parser import store_true, extract_file_names
from powerapi.cli.config_parser import MissingValueException
from powerapi.exception import BadTypeException, BadContextException, UnknownArgException

POWERAPI_ENVIRONMENT_VARIABLE_PREFIX = 'POWERAPI_'
POWERAPI_OUTPUT_ENVIRONMENT_VARIABLE_PREFIX = POWERAPI_ENVIRONMENT_VARIABLE_PREFIX + 'OUTPUT_'
POWERAPI_INPUT_ENVIRONMENT_VARIABLE_PREFIX = POWERAPI_ENVIRONMENT_VARIABLE_PREFIX + 'INPUT_'
POWERAPI_PRE_PROCESSOR_ENVIRONMENT_VARIABLE_PREFIX = POWERAPI_ENVIRONMENT_VARIABLE_PREFIX + 'PRE_PROCESSOR_'
POWERAPI_POST_PROCESSOR_ENVIRONMENT_VARIABLE_PREFIX = POWERAPI_ENVIRONMENT_VARIABLE_PREFIX + 'POST_PROCESSOR'


class CommonCLIParsingManager(RootConfigParsingManager):
    """
    PowerAPI basic config parser
    """

    def __init__(self):
        RootConfigParsingManager.__init__(self)

        # Environment variables prefix

        self.add_argument_prefix(argument_prefix=POWERAPI_ENVIRONMENT_VARIABLE_PREFIX)
        # Subgroups
        self.add_subgroup(name='input',
                          prefix=POWERAPI_INPUT_ENVIRONMENT_VARIABLE_PREFIX,
                          help_text="specify a database input : --input database_name ARG1 ARG2 ... ")

        self.add_subgroup(name='output',
                          prefix=POWERAPI_OUTPUT_ENVIRONMENT_VARIABLE_PREFIX,
                          help_text="specify a database output : --output database_name ARG1 ARG2 ...")

        self.add_subgroup(name='pre-processor',
                          prefix=POWERAPI_PRE_PROCESSOR_ENVIRONMENT_VARIABLE_PREFIX,
                          help_text="specify a pre-processor : --pre-processor pre_processor_name ARG1 ARG2 ...")

        self.add_subgroup(name='post-processor',
                          prefix=POWERAPI_POST_PROCESSOR_ENVIRONMENT_VARIABLE_PREFIX,
                          help_text="specify a post-processor : --post-processor post_processor_name ARG1 ARG2 ...")

        # Parsers

        self.add_argument(
            "v",
            "verbose",
            is_flag=True,
            action=store_true,
            default_value=False,
            help_text="enable verbose mode",
        )
        self.add_argument(
            "s",
            "stream",
            is_flag=True,
            action=store_true,
            default_value=False,
            help_text="enable stream mode",
        )

        subparser_mongo_input = SubgroupConfigParsingManager("mongodb")
        subparser_mongo_input.add_argument("u", "uri", help_text="specify MongoDB uri")
        subparser_mongo_input.add_argument(
            "d",
            "db",
            help_text="specify MongoDB database name",
        )
        subparser_mongo_input.add_argument(
            "c", "collection", help_text="specify MongoDB database collection"
        )
        subparser_mongo_input.add_argument(
            "n", "name", help_text="specify puller name", default_value="puller_mongodb"
        )
        subparser_mongo_input.add_argument(
            "m",
            "model",
            help_text="specify data type that will be stored in the database",
            default_value="HWPCReport",
        )
        self.add_subgroup_parser(
            subgroup_name="input",
            subgroup_parser=subparser_mongo_input
        )

        subparser_socket_input = SubgroupConfigParsingManager("socket")
        subparser_socket_input.add_argument(
            "h", "host", help_text="Specify the host the socket should listen on", default_value='127.0.0.1'
        )
        subparser_socket_input.add_argument(
            "p", "port", help_text="Specify the port the socket should listen on", argument_type=int, default_value=9080,
        )
        subparser_socket_input.add_argument(
            "n", "name", help_text="specify puller name", default_value="puller_socket"
        )
        subparser_socket_input.add_argument(
            "m",
            "model",
            help_text="specify data type that will be sent through the socket",
            default_value="HWPCReport",
        )
        self.add_subgroup_parser(
            subgroup_name="input",
            subgroup_parser=subparser_socket_input
        )

        subparser_csv_input = SubgroupConfigParsingManager("csv")
        subparser_csv_input.add_argument(
            "f",
            "files",
            help_text="specify input csv files with this format : file1,file2,file3",
            action=extract_file_names,
            default_value=[],
        )
        subparser_csv_input.add_argument(
            "m",
            "model",
            help_text="specify data type that will be stored in the database",
            default_value="HWPCReport",
        )
        subparser_csv_input.add_argument(
            "n", "name", help_text="specify puller name", default_value="puller_csv"
        )
        self.add_subgroup_parser(
            subgroup_name="input",
            subgroup_parser=subparser_csv_input
        )

        subparser_mongo_output = SubgroupConfigParsingManager("mongodb")
        subparser_mongo_output.add_argument("u", "uri", help_text="specify MongoDB uri")
        subparser_mongo_output.add_argument(
            "d", "db", help_text="specify MongoDB database name"
        )
        subparser_mongo_output.add_argument(
            "c", "collection", help_text="specify MongoDB database collection"
        )

        subparser_mongo_output.add_argument(
            "m",
            "model",
            help_text="specify data type that will be stored in the database",
            default_value="PowerReport",
        )
        subparser_mongo_output.add_argument(
            "n", "name", help_text="specify pusher name", default_value="pusher_mongodb"
        )
        self.add_subgroup_parser(
            subgroup_name="output",
            subgroup_parser=subparser_mongo_output
        )

        subparser_prometheus_output = SubgroupConfigParsingManager("prometheus")
        subparser_prometheus_output.add_argument(
            "n", "name",
            help_text="Name of the pusher",
            default_value="pusher_prometheus"
        )
        subparser_prometheus_output.add_argument(
            "m", "model",
            help_text="Input report type",
            default_value="PowerReport"
        )
        subparser_prometheus_output.add_argument(
            "u", "uri",
            help_text="Address the HTTP server should listen on",
            default_value="localhost"
        )
        subparser_prometheus_output.add_argument(
            "p", "port",
            help_text="Port number the HTTP server should listen on",
            argument_type=int,
            default_value=8000
        )
        subparser_prometheus_output.add_argument(
            "M", "metric-name",
            help_text="Exposed metric name",
            default_value="power_estimation_watts"
        )
        subparser_prometheus_output.add_argument(
            "d", "metric-description",
            help_text="Set the exposed metric short description",
            default_value="Estimated power consumption of the target"
        )
        subparser_prometheus_output.add_argument(
            "t", "tags",
            help_text="List of metadata tags that will be exposed with the metrics"
        )
        self.add_subgroup_parser(
            subgroup_name="output",
            subgroup_parser=subparser_prometheus_output
        )

        subparser_csv_output = SubgroupConfigParsingManager("csv")
        subparser_csv_output.add_argument(
            "d",
            "directory",
            help_text="specify directory where where output  csv files will be writen",
        )
        subparser_csv_output.add_argument(
            "m",
            "model",
            help_text="specify data type that will be stored in the database",
            default_value="PowerReport",
        )

        subparser_csv_output.add_argument("t", "tags", help_text="List of tags that should be kept")
        subparser_csv_output.add_argument(
            "n", "name", help_text="specify pusher name", default_value="pusher_csv"
        )
        self.add_subgroup_parser(
            subgroup_name="output",
            subgroup_parser=subparser_csv_output
        )

        subparser_opentsdb_output = SubgroupConfigParsingManager("opentsdb")
        subparser_opentsdb_output.add_argument("u", "uri", help_text="specify openTSDB host")
        subparser_opentsdb_output.add_argument(
            "p", "port", help_text="specify openTSDB connection port", argument_type=int
        )
        subparser_opentsdb_output.add_argument(
            "metric-name", help_text="specify metric name"
        )

        subparser_opentsdb_output.add_argument(
            "m",
            "model",
            help_text="specify data type that will be stored in the database",
            default_value="PowerReport",
        )
        subparser_opentsdb_output.add_argument(
            "n", "name", help_text="specify pusher name", default_value="pusher_opentsdb"
        )
        self.add_subgroup_parser(
            subgroup_name="output",
            subgroup_parser=subparser_opentsdb_output
        )

        subparser_influx2_output = SubgroupConfigParsingManager("influxdb2")
        subparser_influx2_output.add_argument("u", "uri", help_text="specify InfluxDB uri")
        subparser_influx2_output.add_argument("t", "tags", help_text="List of tags that should be kept")
        subparser_influx2_output.add_argument("k", "token",
                                              help_text="specify token for accessing the database")
        subparser_influx2_output.add_argument("g", "org",
                                              help_text="specify organisation for accessing the database")

        subparser_influx2_output.add_argument(
            "d", "db", help_text="specify InfluxDB database name"
        )
        subparser_influx2_output.add_argument(
            "p", "port", help_text="specify InfluxDB connection port", argument_type=int
        )
        subparser_influx2_output.add_argument(
            "m",
            "model",
            help_text="specify data type that will be store in the database",
            default_value="PowerReport",
        )
        subparser_influx2_output.add_argument(
            "n", "name", help_text="specify pusher name", default_value="pusher_influxdb2"
        )

        self.add_subgroup_parser(
            subgroup_name="output",
            subgroup_parser=subparser_influx2_output
        )

        subparser_k8s_pre_processor = SubgroupConfigParsingManager("k8s")
        subparser_k8s_pre_processor.add_argument(
            "a",
            "api-mode",
            help_text="Kubernetes API mode (local, manual or cluster)",
            default_value='cluster'
        )

        subparser_k8s_pre_processor.add_argument(
            "k",
            "api-key",
            help_text="Kubernetes Bearer Token (only for manual API mode)",
        )

        subparser_k8s_pre_processor.add_argument(
            "h",
            "api-host",
            help_text="Kubernetes API host (only for manual API mode)",
        )

        subparser_k8s_pre_processor.add_argument(
            "p",
            "puller",
            help_text="Name of the puller to attach the pre-processor to",
        )

        subparser_k8s_pre_processor.add_argument(
            "n",
            "name",
            help_text="Name of the pre-processor"
        )

        self.add_subgroup_parser(
            subgroup_name="pre-processor",
            subgroup_parser=subparser_k8s_pre_processor
        )

    def parse_argv(self):
        """
        Parse command line arguments.
        """
        try:
            return self.parse(sys.argv[1:])

        except MissingValueException as exn:
            msg = "CLI error : argument " + exn.argument_name + " : expect a value"
            print(msg, file=sys.stderr)

        except BadTypeException as exn:
            msg = "Configuration error : " + exn.msg
            print(msg, file=sys.stderr)

        except UnknownArgException as exn:
            msg = "CLI error : unknown argument " + exn.argument_name
            print(msg, file=sys.stderr)

        except BadContextException as exn:
            msg = "CLI error : argument " + exn.argument_name
            msg += " not used in the correct context\nUse it with the following arguments :"
            for main_arg_name, context_name in exn.context_list:
                msg += "\n  --" + main_arg_name + " " + context_name
            print(msg, file=sys.stderr)

        sys.exit()
