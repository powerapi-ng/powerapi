# Copyright (c) 2021, Inria
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

from powerapi.cli.config_parser import store_true
from powerapi.cli.parsing_manager import RootConfigParsingManager, SubgroupConfigParsingManager


def generate_env_prefix(*components: str, root_prefix: str = 'POWERAPI') -> str:
    """
    Generate the environment variable prefix from the given components.
    :param components: Additional prefix components.
    :param root_prefix: Root namespace for the prefix.
    :return: The normalized environment variable prefix.
    """
    return '_'.join(
        normalized_part.upper() for part in (root_prefix, *components) if (normalized_part := part.strip())
    ) + '_'


class PullerConfigParsingManager(SubgroupConfigParsingManager):
    """
    Subgroup parser with arguments shared by every puller input.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a puller parser with common actor name and report model arguments.
        """
        super().__init__(name)

        self.add_argument(
            'n', 'name',
            help_text='Name assigned to this puller actor'
        )
        self.add_argument(
            'm', 'model',
            help_text='Report type produced by this input source',
            default_value='HWPCReport'
        )


class PusherConfigParsingManager(SubgroupConfigParsingManager):
    """
    Subgroup parser with arguments shared by every pusher output.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a pusher parser with common actor name and report model arguments.
        """
        super().__init__(name)

        self.add_argument(
            'n', 'name',
            help_text='Name assigned to this pusher actor'
        )
        self.add_argument(
            'm', 'model',
            help_text='Report type consumed by this output destination',
            default_value='PowerReport'
        )


class PreProcessorConfigParsingManager(SubgroupConfigParsingManager):
    """
    Subgroup parser with arguments shared by every pre-processor.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a pre-processor parser with common actor name and puller binding arguments.
        """
        super().__init__(name)

        self.add_argument(
            'n', 'name',
            help_text='Name assigned to this pre-processor actor'
        )
        self.add_argument(
            'p', 'puller',
            help_text='Name of the puller actor this pre-processor receives reports from',
            is_mandatory=True,
        )


class CommonCLIParsingManager(RootConfigParsingManager):
    """
    Root parser that registers PowerAPI's built-in CLI component options.
    """

    def __init__(self) -> None:
        """
        Initialize the root parser and register all built-in component parsers.
        """
        super().__init__()

        self._register_environment_prefixes()
        self._register_subgroups()
        self._register_root_arguments()
        self._register_input_parsers()
        self._register_output_parsers()
        self._register_pre_processor_parsers()

    def _register_environment_prefixes(self) -> None:
        """
        Register environment variable prefixes accepted by the root parser.
        """
        self.add_argument_prefix(generate_env_prefix())

    def _register_subgroups(self) -> None:
        """
        Register top-level component groups accepted by the CLI.
        """
        self.add_subgroup(
            name='input',
            prefix=generate_env_prefix('INPUT'),
            help_text='Configure an input source: --input TYPE OPTIONS'
        )
        self.add_subgroup(
            name='output',
            prefix=generate_env_prefix('OUTPUT'),
            help_text='Configure an output destination: --output TYPE OPTIONS'
        )
        self.add_subgroup(
            name='pre-processor',
            prefix=generate_env_prefix('PRE_PROCESSOR'),
            help_text='Configure a pre-processor: --pre-processor TYPE OPTIONS'
        )
        self.add_subgroup(
            name='post-processor',
            prefix=generate_env_prefix('POST_PROCESSOR'),
            help_text='Configure a post-processor: --post-processor TYPE OPTIONS'
        )

    def _register_root_arguments(self) -> None:
        """
        Register root-level options that apply to the whole PowerAPI process.
        """
        self.add_argument(
            'v', 'verbose',
            is_flag=True,
            action=store_true,
            default_value=False,
            help_text='Enable verbose logging',
        )
        self.add_argument(
            's', 'stream',
            is_flag=True,
            action=store_true,
            default_value=False,
            help_text='Enable stream processing mode',
        )

    def _register_input_parsers(self):
        """
        Register all built-in input source parsers.
        """
        self._register_mongodb_input_parser()
        self._register_socket_input_parser()
        self._register_csv_input_parser()
        self._register_json_input_parser()

    def _register_mongodb_input_parser(self):
        """
        Register the MongoDB input parser.
        """
        subparser_mongo_input = PullerConfigParsingManager('mongodb')

        subparser_mongo_input.add_argument(
            'u', 'uri',
            help_text='MongoDB connection URI',
            is_mandatory=True
        )
        subparser_mongo_input.add_argument(
            'd', 'db',
            help_text='MongoDB database name',
            is_mandatory=True
        )
        subparser_mongo_input.add_argument(
            'c', 'collection',
            help_text='MongoDB collection name',
            is_mandatory=True
        )

        self.add_subgroup_parser('input', subparser_mongo_input)

    def _register_socket_input_parser(self):
        """
        Register the Socket input parser.
        """
        subparser_socket_input = PullerConfigParsingManager('socket')

        subparser_socket_input.add_argument(
            'h', 'host',
            help_text='Host address the socket listens on',
            default_value='localhost'
        )
        subparser_socket_input.add_argument(
            'p', 'port',
            help_text="Port number the socket listens on",
            argument_type=int,
            default_value=9080,
        )

        self.add_subgroup_parser('input', subparser_socket_input)

    def _register_csv_input_parser(self):
        """
        Register the CSV input parser.
        """
        subparser_csv_input = PullerConfigParsingManager('csv')

        subparser_csv_input.add_argument(
            'f', 'files',
            help_text='Comma-separated list of CSV input files',
            argument_type=list,
            is_mandatory=True
        )

        self.add_subgroup_parser('input', subparser_csv_input)

    def _register_json_input_parser(self):
        """
        Register the JSON input parser.
        """
        subparser_json_input = PullerConfigParsingManager('json')

        subparser_json_input.add_argument(
            'f', 'filepath',
            help_text='Path to the JSON input file',
            is_mandatory=True
        )
        subparser_json_input.add_argument(
            'c', 'compression',
            help_text='Input compression format: auto, gzip, lzma, or none',
            default_value='auto'
        )

        self.add_subgroup_parser('input', subparser_json_input)

    def _register_output_parsers(self):
        """
        Register all built-in output destination parsers.
        """
        self._register_mongodb_output_parser()
        self._register_prometheus_output_parser()
        self._register_csv_output_parser()
        self._register_json_output_parser()
        self._register_influxdb2_output_parser()

    def _register_mongodb_output_parser(self):
        """
        Register the MongoDB output parser.
        """
        subparser_mongo_output = PusherConfigParsingManager('mongodb')

        subparser_mongo_output.add_argument(
            'u', 'uri',
            help_text='MongoDB connection URI',
            is_mandatory=True
        )
        subparser_mongo_output.add_argument(
            'd', 'db',
            help_text='MongoDB database name',
            is_mandatory=True
        )
        subparser_mongo_output.add_argument(
            'c', 'collection',
            help_text='MongoDB collection name',
            is_mandatory=True
        )

        self.add_subgroup_parser('output', subparser_mongo_output)

    def _register_prometheus_output_parser(self):
        """
        Register the Prometheus output parser.
        """
        subparser_prometheus_output = PusherConfigParsingManager('prometheus')

        subparser_prometheus_output.add_argument(
            'u', 'addr',
            help_text='Host address the Prometheus HTTP server listens on',
            default_value='localhost'
        )
        subparser_prometheus_output.add_argument(
            'p', 'port',
            help_text='Port number the Prometheus HTTP server listens on',
            argument_type=int,
            default_value=8000
        )
        subparser_prometheus_output.add_argument(
            'M', 'metric-name',
            help_text='Prometheus metric name to expose',
            default_value='power_estimation_watts'
        )
        subparser_prometheus_output.add_argument(
            'd', 'metric-description',
            help_text='Prometheus metric description',
            default_value='Estimated power consumption of the target'
        )
        subparser_prometheus_output.add_argument(
            't', 'tags',
            help_text='Comma-separated list of report metadata fields exposed as metric labels',
            argument_type=list
        )

        self.add_subgroup_parser('output', subparser_prometheus_output)

    def _register_csv_output_parser(self):
        """
        Register the CSV output parser.
        """
        subparser_csv_output = PusherConfigParsingManager('csv')

        subparser_csv_output.add_argument(
            'd', 'directory',
            help_text='Directory where CSV output files are written',
            is_mandatory=True
        )

        self.add_subgroup_parser('output', subparser_csv_output)

    def _register_json_output_parser(self):
        """
        Register the JSON output parser.
        """
        subparser_json_output = PusherConfigParsingManager('json')

        subparser_json_output.add_argument(
            'f', 'filepath',
            help_text='Path to the JSON output file',
            is_mandatory=True
        )
        subparser_json_output.add_argument(
            'c', 'compression',
            help_text='Output compression format: auto, gzip, lzma, or none',
            default_value='auto'
        )

        self.add_subgroup_parser('output', subparser_json_output)

    def _register_influxdb2_output_parser(self):
        """
        Register the InfluxDB 2 output parser.
        """
        subparser_influx2_output = PusherConfigParsingManager('influxdb2')

        subparser_influx2_output.add_argument(
            'u', 'uri',
            help_text='InfluxDB server URI',
            is_mandatory=True
        )
        subparser_influx2_output.add_argument(
            'k', 'token',
            help_text='InfluxDB API token',
            is_mandatory=True
        )
        subparser_influx2_output.add_argument(
            'g', 'org',
            help_text='InfluxDB organization name',
            is_mandatory=True
        )
        subparser_influx2_output.add_argument(
            'b', 'bucket',
            help_text='InfluxDB bucket name',
            is_mandatory=True
        )

        self.add_subgroup_parser('output', subparser_influx2_output)

    def _register_pre_processor_parsers(self):
        """
        Register all built-in pre-processor parsers.
        """
        self._register_k8s_pre_processor_parser()
        self._register_openstack_pre_processor_parser()

    def _register_k8s_pre_processor_parser(self):
        """
        Register the Kubernetes pre-processor parser.
        """
        subparser_k8s_pre_processor = PreProcessorConfigParsingManager('k8s')

        subparser_k8s_pre_processor.add_argument(
            'a', 'api-mode',
            help_text='Kubernetes API access mode: local, manual, or cluster',
            default_value='cluster'
        )

        subparser_k8s_pre_processor.add_argument(
            'k', 'api-key',
            help_text='Kubernetes bearer token for manual API mode',
        )

        subparser_k8s_pre_processor.add_argument(
            'h', 'api-host',
            help_text='Kubernetes API host for manual API mode',
        )

        self.add_subgroup_parser('pre-processor', subparser_k8s_pre_processor)

    def _register_openstack_pre_processor_parser(self):
        """
        Register the OpenStack pre-processor parser.
        """
        subparser_openstack_pre_processor = PreProcessorConfigParsingManager('openstack')

        subparser_openstack_pre_processor.add_argument(
            'i', "polling-interval",
            help_text='OpenStack API polling interval in seconds',
            argument_type=float,
            default_value=10.0
        )

        self.add_subgroup_parser('pre-processor', subparser_openstack_pre_processor)
