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

from powerapi.cli.config_parser import ComponentSchema
from powerapi.cli.parsing_manager import ConfigurationParsingManager


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


class PullerSchema(ComponentSchema):
    """
    Component schema with arguments shared by every puller input.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a puller schema with the common report model argument.
        """
        super().__init__(name)

        self.add_argument(
            'model',
            help_text='Report type produced by this input source',
            default_value='HWPCReport'
        )


class PusherSchema(ComponentSchema):
    """
    Component schema with arguments shared by every pusher output.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a pusher schema with the common report model argument.
        """
        super().__init__(name)

        self.add_argument(
            'model',
            help_text='Report type consumed by this output destination',
            default_value='PowerReport'
        )


class PreProcessorSchema(ComponentSchema):
    """
    Component schema with arguments shared by every pre-processor.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a pre-processor schema with the puller binding argument.
        """
        super().__init__(name)

        self.add_argument(
            'puller',
            help_text='Name of the puller actor this pre-processor receives reports from',
            is_mandatory=True,
        )


class CommonCLIParsingManager(ConfigurationParsingManager):
    """
    Configuration manager that registers PowerAPI's built-in CLI component options.
    """

    def __init__(self) -> None:
        """
        Initialize the configuration manager and register all built-in component schemas.
        """
        super().__init__()

        self._register_environment_prefixes()
        self._register_groups()
        self._register_root_arguments()
        self._register_input_schemas()
        self._register_output_schemas()
        self._register_pre_processor_schemas()

    def _register_environment_prefixes(self) -> None:
        """
        Register environment variable prefixes accepted by the configuration manager.
        """
        self.add_argument_prefix(generate_env_prefix())

    def _register_groups(self) -> None:
        """
        Register top-level component groups accepted by the CLI.
        """
        self.add_group(
            name='input',
            prefix=generate_env_prefix('INPUT'),
            help_text='Configure an input source with -C input.NAME.PROPERTY=VALUE'
        )
        self.add_group(
            name='output',
            prefix=generate_env_prefix('OUTPUT'),
            help_text='Configure an output destination with -C output.NAME.PROPERTY=VALUE'
        )
        self.add_group(
            name='pre-processor',
            prefix=generate_env_prefix('PRE_PROCESSOR'),
            help_text='Configure a pre-processor with -C pre-processor.NAME.PROPERTY=VALUE'
        )
        self.add_group(
            name='post-processor',
            prefix=generate_env_prefix('POST_PROCESSOR'),
            help_text='Configure a post-processor with -C post-processor.NAME.PROPERTY=VALUE'
        )

    def _register_root_arguments(self) -> None:
        """
        Register root-level options that apply to the whole PowerAPI process.
        """
        self.add_argument(
            'verbose',
            is_flag=True,
            default_value=False,
            help_text='Enable verbose logging',
        )
        self.add_argument(
            'stream',
            is_flag=True,
            default_value=False,
            help_text='Enable stream processing mode',
        )

    def _register_input_schemas(self):
        """
        Register all built-in input source schemas.
        """
        self._register_mongodb_input_schema()
        self._register_socket_input_schema()
        self._register_csv_input_schema()
        self._register_json_input_schema()

    def _register_mongodb_input_schema(self):
        """
        Register the MongoDB input schema.
        """
        schema_mongo_input = PullerSchema('mongodb')

        schema_mongo_input.add_argument(
            'uri',
            help_text='MongoDB connection URI',
            is_mandatory=True
        )
        schema_mongo_input.add_argument(
            'db',
            help_text='MongoDB database name',
            is_mandatory=True
        )
        schema_mongo_input.add_argument(
            'collection',
            help_text='MongoDB collection name',
            is_mandatory=True
        )

        self.add_component('input', schema_mongo_input)

    def _register_socket_input_schema(self):
        """
        Register the Socket input schema.
        """
        schema_socket_input = PullerSchema('socket')

        schema_socket_input.add_argument(
            'host',
            help_text='Host address the socket listens on',
            default_value='localhost'
        )
        schema_socket_input.add_argument(
            'port',
            help_text="Port number the socket listens on",
            argument_type=int,
            default_value=9080,
        )

        self.add_component('input', schema_socket_input)

    def _register_csv_input_schema(self):
        """
        Register the CSV input schema.
        """
        schema_csv_input = PullerSchema('csv')

        schema_csv_input.add_argument(
            'files',
            help_text='Comma-separated list of CSV input files',
            argument_type=list,
            is_mandatory=True
        )

        self.add_component('input', schema_csv_input)

    def _register_json_input_schema(self):
        """
        Register the JSON input schema.
        """
        schema_json_input = PullerSchema('json')

        schema_json_input.add_argument(
            'filepath',
            help_text='Path to the JSON input file',
            is_mandatory=True
        )
        schema_json_input.add_argument(
            'compression',
            help_text='Input compression format: auto, gzip, lzma, or none',
            default_value='auto'
        )

        self.add_component('input', schema_json_input)

    def _register_output_schemas(self):
        """
        Register all built-in output destination schemas.
        """
        self._register_mongodb_output_schema()
        self._register_prometheus_output_schema()
        self._register_csv_output_schema()
        self._register_json_output_schema()
        self._register_influxdb2_output_schema()
        self._register_clickhouse_output_schema()

    def _register_mongodb_output_schema(self):
        """
        Register the MongoDB output schema.
        """
        schema_mongo_output = PusherSchema('mongodb')

        schema_mongo_output.add_argument(
            'uri',
            help_text='MongoDB connection URI',
            is_mandatory=True
        )
        schema_mongo_output.add_argument(
            'db',
            help_text='MongoDB database name',
            is_mandatory=True
        )
        schema_mongo_output.add_argument(
            'collection',
            help_text='MongoDB collection name',
            is_mandatory=True
        )

        self.add_component('output', schema_mongo_output)

    def _register_prometheus_output_schema(self):
        """
        Register the Prometheus output schema.
        """
        schema_prometheus_output = PusherSchema('prometheus')

        schema_prometheus_output.add_argument(
            'addr',
            help_text='Host address the Prometheus HTTP server listens on',
            default_value='localhost'
        )
        schema_prometheus_output.add_argument(
            'port',
            help_text='Port number the Prometheus HTTP server listens on',
            argument_type=int,
            default_value=8000
        )
        schema_prometheus_output.add_argument(
            'tags',
            help_text='Comma-separated list of report metadata fields exposed as metric labels',
            argument_type=list
        )

        self.add_component('output', schema_prometheus_output)

    def _register_csv_output_schema(self):
        """
        Register the CSV output schema.
        """
        schema_csv_output = PusherSchema('csv')

        schema_csv_output.add_argument(
            'directory',
            help_text='Directory where CSV output files are written',
            is_mandatory=True
        )

        self.add_component('output', schema_csv_output)

    def _register_json_output_schema(self):
        """
        Register the JSON output schema.
        """
        schema_json_output = PusherSchema('json')

        schema_json_output.add_argument(
            'filepath',
            help_text='Path to the JSON output file',
            is_mandatory=True
        )
        schema_json_output.add_argument(
            'compression',
            help_text='Output compression format: auto, gzip, lzma, or none',
            default_value='auto'
        )

        self.add_component('output', schema_json_output)

    def _register_influxdb2_output_schema(self):
        """
        Register the InfluxDB 2 output schema.
        """
        schema_influx2_output = PusherSchema('influxdb2')

        schema_influx2_output.add_argument(
            'uri',
            help_text='InfluxDB server URI',
            is_mandatory=True
        )
        schema_influx2_output.add_argument(
            'token',
            help_text='InfluxDB API token',
            is_mandatory=True
        )
        schema_influx2_output.add_argument(
            'org',
            help_text='InfluxDB organization name',
            is_mandatory=True
        )
        schema_influx2_output.add_argument(
            'bucket',
            help_text='InfluxDB bucket name',
            is_mandatory=True
        )

        self.add_component('output', schema_influx2_output)

    def _register_clickhouse_output_schema(self):
        """
        Register the ClickHouse output schema.
        """
        schema_clickhouse_output = PusherSchema('clickhouse')

        schema_clickhouse_output.add_argument(
            'host',
            help_text='ClickHouse server host',
            is_mandatory=True,
        )
        schema_clickhouse_output.add_argument(
            'port',
            help_text='ClickHouse server port',
            argument_type=int,
            default_value=8123,
        )
        schema_clickhouse_output.add_argument(
            'username',
            help_text='ClickHouse username',
            default_value='default',
        )
        schema_clickhouse_output.add_argument(
            'password',
            help_text='ClickHouse password',
            default_value='',
        )
        schema_clickhouse_output.add_argument(
            'database',
            help_text='ClickHouse database name',
            default_value='default',
        )

        self.add_component('output', schema_clickhouse_output)

    def _register_pre_processor_schemas(self):
        """
        Register all built-in pre-processor schemas.
        """
        self._register_k8s_pre_processor_schema()
        self._register_openstack_pre_processor_schema()

    def _register_k8s_pre_processor_schema(self):
        """
        Register the Kubernetes pre-processor schema.
        """
        schema_k8s_pre_processor = PreProcessorSchema('kubernetes')

        schema_k8s_pre_processor.add_argument(
            'api-mode',
            help_text='Kubernetes API access mode: local, manual, or cluster',
            default_value='cluster'
        )

        schema_k8s_pre_processor.add_argument(
            'api-key',
            help_text='Kubernetes bearer token for manual API mode',
        )

        schema_k8s_pre_processor.add_argument(
            'api-host',
            help_text='Kubernetes API host for manual API mode',
        )

        schema_k8s_pre_processor.add_argument(
            'labels',
            help_text='Comma-separated list of Kubernetes pod labels added to reports as metadata',
            argument_type=list
        )

        self.add_component('pre-processor', schema_k8s_pre_processor)

    def _register_openstack_pre_processor_schema(self):
        """
        Register the OpenStack pre-processor schema.
        """
        schema_openstack_pre_processor = PreProcessorSchema('openstack')

        schema_openstack_pre_processor.add_argument(
            'polling-interval',
            help_text='OpenStack API polling interval in seconds',
            argument_type=float,
            default_value=10.0
        )

        schema_openstack_pre_processor.add_argument(
            'metadata',
            help_text='Comma-separated list of OpenStack server metadata fields added to reports',
            argument_type=list
        )

        self.add_component('pre-processor', schema_openstack_pre_processor)
