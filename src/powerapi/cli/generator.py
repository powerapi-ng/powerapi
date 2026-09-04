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

import logging
from collections.abc import Callable

from powerapi.actor import Actor, ActorProxy
from powerapi.database.driver import ReadableDatabaseFactory, WritableDatabaseFactory
from powerapi.exception import ConfigurationError, PowerAPIException
from powerapi.filter import ReportFilter
from powerapi.processor.processor_actor import ProcessorActor
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor
from powerapi.report import FormulaReport, HWPCReport, PowerReport, Report
from powerapi.utils.metadata import build_metadata_mapping

COMPONENT_TYPE_KEY = 'type'
COMPONENT_MODEL_KEY = 'model'

ACTOR_NAME_KEY = 'actor_name'

GENERAL_CONF_STREAM_MODE_KEY = 'stream'
GENERAL_CONF_VERBOSE_KEY = 'verbose'

_NON_STREAMING_INPUT_TYPES = frozenset(('csv', 'json'))


class Generator[ActorT: Actor]:
    """
    Generate actors for one configured component group.
    """

    def __init__(self, component_group_name: str):
        """
        Initialize a generator for a component group.
        :param component_group_name: Name of the component group to generate.
        """
        self.component_group_name = component_group_name

    def generate(self, main_config: dict) -> dict[str, ActorT]:
        """
        Generate every actor configured in the component group.
        :param main_config: Canonical PowerAPI configuration.
        :return: Generated actors indexed by component name.
        :raises PowerAPIException: If the component group is missing or a component configuration is invalid.
        """
        if self.component_group_name not in main_config:
            raise PowerAPIException(f'Configuration error: Component "{self.component_group_name}" is not defined')

        actors = {}
        for component_name, component_config in main_config[self.component_group_name].items():
            actors[component_name] = self._gen_actor(component_config, main_config, component_name)

        return actors

    def _gen_actor(self, component_config: dict, main_config: dict, component_name: str) -> ActorT:
        """
        Generate one actor from its component configuration.
        :param component_config: Canonical component configuration.
        :param main_config: Canonical PowerAPI configuration.
        :param component_name: Name of the component to generate.
        :return: Generated actor.
        """
        raise NotImplementedError()


class DBActorGenerator[ActorT: Actor, DBFactoryT: ReadableDatabaseFactory | WritableDatabaseFactory](Generator[ActorT]):
    """
    Resolve database factories before generating database-backed actors.
    """

    def __init__(self, component_group_name: str):
        """
        Initialize a database-backed actor generator.
        :param component_group_name: Name of the component group to generate.
        """
        super().__init__(component_group_name)
        self.report_classes: dict[str, type[Report]] = {
            'HWPCReport': HWPCReport,
            'PowerReport': PowerReport,
            'FormulaReport': FormulaReport,
        }
        self.database_factories: dict[str, Callable[[dict], DBFactoryT]] = {}

    def _get_report_class(self, model_name: str) -> type[Report]:
        """
        Resolve a configured report model name.
        :param model_name: Registered report model name.
        :return: Report class registered for the configured model.
        :raises PowerAPIException: If the report model is unknown.
        """
        try:
            return self.report_classes[model_name]
        except KeyError as error:
            raise PowerAPIException(f'Configuration error: Unknown report model "{model_name}"') from error

    def add_report_class(self, model_name: str, report_class: type[Report]):
        """
        Register a report class.
        :param model_name: Name identifying the report model.
        :param report_class: Report class associated with the model name.
        :raises ValueError: If the report model is already registered.
        """
        if model_name in self.report_classes:
            raise ValueError(f'Report model "{model_name}" is already registered')

        self.report_classes[model_name] = report_class

    def add_db_factory(self, db_name: str, db_factory_function: Callable[[dict], DBFactoryT]):
        """
        Register a database factory.
        :param db_name: Database type handled by the factory.
        :param db_factory_function: Function creating a database factory from component configuration.
        :raises ValueError: If the database type is already registered.
        """
        if db_name in self.database_factories:
            raise ValueError(f'Database type "{db_name}" is already registered')

        self.database_factories[db_name] = db_factory_function

    def _create_database_factory(self, db_name: str, component_config: dict) -> DBFactoryT:
        """
        Create a database factory for a component.
        :param db_name: Registered database type.
        :param component_config: Canonical component configuration.
        :return: Configured readable or writable database factory.
        :raises PowerAPIException: If the database type is unknown or its optional dependencies are unavailable.
        """
        try:
            factory = self.database_factories[db_name]
        except KeyError as error:
            raise PowerAPIException(f'Configuration error: Invalid database type: {db_name}') from error

        try:
            return factory(component_config)
        except ImportError as error:
            raise PowerAPIException(f'Dependencies for {db_name} database are not installed') from error

    def _gen_actor(self, component_config: dict, main_config: dict, component_name: str) -> ActorT:
        """
        Resolve the report model and database factory before generating an actor.
        :param component_config: Canonical component configuration.
        :param main_config: Canonical PowerAPI configuration.
        :param component_name: Name of the component to generate.
        :return: Generated database-backed actor.
        :raises PowerAPIException: If the report model or database type is unknown or a dependency is unavailable.
        """
        factory_config = dict(component_config)
        factory_config[COMPONENT_MODEL_KEY] = self._get_report_class(component_config[COMPONENT_MODEL_KEY])
        database_factory = self._create_database_factory(
            component_config[COMPONENT_TYPE_KEY],
            factory_config,
        )

        return self._actor_factory(component_name, main_config, database_factory)

    def _actor_factory(self, actor_name: str, main_config: dict, database_factory: DBFactoryT) -> ActorT:
        """
        Create a database-backed actor from a resolved component configuration.
        :param actor_name: Name assigned to the actor.
        :param main_config: Canonical PowerAPI configuration.
        :param database_factory: Configured database factory.
        :return: Generated actor.
        """
        raise NotImplementedError


class PullerGenerator(DBActorGenerator[PullerActor, ReadableDatabaseFactory]):
    """
    Generate puller actors from input component configurations.
    """

    @staticmethod
    def _csv_input_database_factory(conf: dict) -> ReadableDatabaseFactory:
        """
        Create a CSV input database factory.
        :param conf: Canonical CSV input configuration.
        :return: Configured CSV input factory.
        """
        from powerapi.database.csv.driver import CSVInputFactory
        return CSVInputFactory(conf['model'], conf['files'])

    @staticmethod
    def _json_input_database_factory(conf: dict) -> ReadableDatabaseFactory:
        """
        Create a JSON input database factory.
        :param conf: Canonical JSON input configuration.
        :return: Configured JSON input factory.
        """
        from powerapi.database.json.driver import JsonInputFactory
        return JsonInputFactory(conf['model'], conf['filepath'], conf['compression'])

    @staticmethod
    def _socket_database_factory(conf: dict) -> ReadableDatabaseFactory:
        """
        Create a socket input database factory.
        :param conf: Canonical socket input configuration.
        :return: Configured socket input factory.
        """
        from powerapi.database.socket.driver import SocketInputFactory
        return SocketInputFactory(conf['model'], conf['host'], conf['port'])

    @staticmethod
    def _mongodb_database_factory(conf: dict) -> ReadableDatabaseFactory:
        """
        Create a MongoDB input database factory.
        :param conf: Canonical MongoDB input configuration.
        :return: Configured MongoDB input factory.
        """
        from powerapi.database.mongodb.driver import MongodbInputFactory
        return MongodbInputFactory(conf['model'], conf['uri'], conf['db'], conf['collection'])

    def __init__(self, report_filter: ReportFilter):
        """
        Initialize a puller generator with the built-in input types.
        :param report_filter: Report filter applied to incoming reports.
        """
        super().__init__('input')

        self.report_filter = report_filter

        self.add_db_factory('csv', self._csv_input_database_factory)
        self.add_db_factory('json', self._json_input_database_factory)
        self.add_db_factory('socket', self._socket_database_factory)
        self.add_db_factory('mongodb', self._mongodb_database_factory)

    def _gen_actor(self, component_config: dict, main_config: dict, component_name: str) -> PullerActor:
        """
        Generate a puller after checking that its input supports the configured execution mode.
        :param component_config: Canonical input component configuration.
        :param main_config: Canonical PowerAPI configuration.
        :param component_name: Name of the input component.
        :return: Configured puller actor.
        :raises ConfigurationError: If stream mode is enabled for a non-streaming input type.
        """
        input_type = component_config[COMPONENT_TYPE_KEY]
        if main_config[GENERAL_CONF_STREAM_MODE_KEY] and input_type in _NON_STREAMING_INPUT_TYPES:
            raise ConfigurationError(f'Stream mode cannot be used with a {input_type} input', GENERAL_CONF_STREAM_MODE_KEY)

        return super()._gen_actor(component_config, main_config, component_name)

    def _actor_factory(self, actor_name: str, main_config: dict, database_factory: ReadableDatabaseFactory) -> PullerActor:
        """
        Create a puller actor.
        :param actor_name: Name assigned to the actor.
        :param main_config: Canonical PowerAPI configuration.
        :param database_factory: Configured readable database factory.
        :return: Configured puller actor.
        """
        stream_mode = main_config[GENERAL_CONF_STREAM_MODE_KEY]
        logging_level = logging.DEBUG if main_config[GENERAL_CONF_VERBOSE_KEY] else logging.WARNING
        return PullerActor(actor_name, database_factory, self.report_filter, stream_mode, level_logger=logging_level)


class PusherGenerator(DBActorGenerator[PusherActor, WritableDatabaseFactory]):
    """
    Generate pusher actors from output component configurations.
    """

    @staticmethod
    def _csv_output_database_factory(conf: dict) -> WritableDatabaseFactory:
        """
        Create a CSV output database factory.
        :param conf: Canonical CSV output configuration.
        :return: Configured CSV output factory.
        """
        from powerapi.database.csv.driver import CSVOutputFactory
        return CSVOutputFactory(conf['model'], conf['directory'])

    @staticmethod
    def _json_output_database_factory(conf: dict) -> WritableDatabaseFactory:
        """
        Create a JSON output database factory.
        :param conf: Canonical JSON output configuration.
        :return: Configured JSON output factory.
        """
        from powerapi.database.json.driver import JsonOutputFactory
        return JsonOutputFactory(conf['model'], conf['filepath'], conf['compression'])

    @staticmethod
    def _mongodb_database_factory(conf: dict) -> WritableDatabaseFactory:
        """
        Create a MongoDB output database factory.
        :param conf: Canonical MongoDB output configuration.
        :return: Configured MongoDB output factory.
        """
        from powerapi.database.mongodb.driver import MongodbOutputFactory
        return MongodbOutputFactory(conf['model'], conf['uri'], conf['db'], conf['collection'])

    @staticmethod
    def _influxdb2_database_factory(conf: dict) -> WritableDatabaseFactory:
        """
        Create an InfluxDB 2 output database factory.
        :param conf: Canonical InfluxDB 2 output configuration.
        :return: Configured InfluxDB 2 output factory.
        """
        from powerapi.database.influxdb2.driver import InfluxDB2OutputFactory
        return InfluxDB2OutputFactory(conf['model'], conf['uri'], conf['org'], conf['bucket'], conf['token'])

    @staticmethod
    def _prometheus_database_factory(conf: dict) -> WritableDatabaseFactory:
        """
        Create a Prometheus output database factory.
        :param conf: Canonical Prometheus output configuration.
        :return: Configured Prometheus output factory.
        """
        from powerapi.database.prometheus.driver import PrometheusOutputFactory
        return PrometheusOutputFactory(conf['model'], conf['addr'], conf['port'], conf.get('tags', []))

    @staticmethod
    def _clickhouse_database_factory(conf: dict) -> WritableDatabaseFactory:
        """
        Create a ClickHouse output database factory.
        :param conf: Canonical ClickHouse output configuration.
        :return: Configured ClickHouse output factory.
        """
        from powerapi.database.clickhouse.driver import ClickHouseOutputFactory
        return ClickHouseOutputFactory(conf['model'], conf['host'], conf['port'], conf['username'], conf['password'], conf['database'])

    def __init__(self):
        """
        Initialize a pusher generator with the built-in output types.
        """
        super().__init__('output')

        self.add_db_factory('csv', self._csv_output_database_factory)
        self.add_db_factory('json', self._json_output_database_factory)
        self.add_db_factory('mongodb', self._mongodb_database_factory)
        self.add_db_factory('influxdb2', self._influxdb2_database_factory)
        self.add_db_factory('prometheus', self._prometheus_database_factory)
        self.add_db_factory('clickhouse', self._clickhouse_database_factory)

    def _actor_factory(self, actor_name: str, main_config: dict, database_factory: WritableDatabaseFactory) -> PusherActor:
        """
        Create a pusher actor.
        :param actor_name: Name assigned to the actor.
        :param main_config: Canonical PowerAPI configuration.
        :param database_factory: Configured writable database factory.
        :return: Configured pusher actor.
        """
        level_logger = logging.DEBUG if main_config[GENERAL_CONF_VERBOSE_KEY] else logging.WARNING
        return PusherActor(actor_name, database_factory, logger_level=level_logger)

    def generate_report_mapping(self, main_config: dict, actors: dict[str, PusherActor]) -> dict[type[Report], list[ActorProxy]]:
        """
        Map report types to generated pusher proxies.
        :param main_config: Canonical PowerAPI configuration.
        :param actors: Generated pusher actors indexed by component name.
        :return: Pusher proxies indexed by report type.
        :raises PowerAPIException: If the output group or a configured actor is missing.
        """
        if self.component_group_name not in main_config:
            raise PowerAPIException(f'Configuration error: Component "{self.component_group_name}" is not defined')

        report_type_to_actor = {}
        for component_name, component_config in main_config[self.component_group_name].items():
            try:
                actor_proxy = actors[component_name].get_proxy()
            except KeyError as error:
                raise PowerAPIException(f'Actor "{component_name}" is not defined') from error

            report_type = self._get_report_class(component_config[COMPONENT_MODEL_KEY])
            report_type_to_actor.setdefault(report_type, []).append(actor_proxy)

        return report_type_to_actor


class ProcessorGenerator(Generator[ProcessorActor]):
    """
    Generator that initializes the processor actor(s) from the configuration.
    """

    def __init__(self, component_group_name: str):
        """
        Initialize a processor generator.
        :param component_group_name: Name of the component group to generate.
        """
        super().__init__(component_group_name)

        self.processor_factories: dict[str, Callable[[dict], ProcessorActor]] = {}

    def add_processor_factory(self, processor_type: str, processor_factory_function: Callable[[dict], ProcessorActor]) -> None:
        """
        Register a processor actor factory.
        :param processor_type: Processor type handled by the factory.
        :param processor_factory_function: Function creating a processor actor from component configuration.
        :raises ValueError: If the processor type is already registered.
        """
        if processor_type in self.processor_factories:
            raise ValueError(f'Processor type "{processor_type}" is already registered')

        self.processor_factories[processor_type] = processor_factory_function

    def _create_processor(self, processor_name: str, component_config: dict) -> ProcessorActor:
        """
        Create a processor actor for a component.
        :param processor_name: Registered processor type.
        :param component_config: Resolved processor component configuration.
        :return: Configured processor actor.
        :raises PowerAPIException: If the processor type is unknown or its optional dependencies are unavailable.
        """
        try:
            factory = self.processor_factories[processor_name]
        except KeyError as error:
            raise PowerAPIException(f'Configuration error: Invalid processor type: {processor_name}') from error

        try:
            return factory(component_config)
        except ImportError as error:
            raise PowerAPIException(f'Dependencies for {processor_name} processor are not installed') from error

    def _gen_actor(self, component_config: dict, main_config: dict, component_name: str) -> ProcessorActor:
        """
        Add shared processor settings and generate one processor actor.
        :param component_config: Canonical component configuration.
        :param main_config: Canonical PowerAPI configuration.
        :param component_name: Name of the processor actor to generate.
        :return: Configured processor actor.
        :raises PowerAPIException: If the processor type is unknown or its optional dependencies are unavailable.
        """
        runtime_config = dict(component_config)
        processor_actor_type = component_config[COMPONENT_TYPE_KEY]
        runtime_config[ACTOR_NAME_KEY] = component_name
        runtime_config[GENERAL_CONF_VERBOSE_KEY] = main_config[GENERAL_CONF_VERBOSE_KEY]
        return self._create_processor(processor_actor_type, runtime_config)


class PreProcessorGenerator(ProcessorGenerator):
    """
    Generator that initializes the pre-processor actor(s) from the configuration.
    """

    def __init__(self):
        """
        Initialize a pre-processor generator with the built-in processor types.
        """
        super().__init__('pre-processor')

        self.add_processor_factory('kubernetes', self._k8s_pre_processor_factory)
        self.add_processor_factory('openstack', self._openstack_pre_processor_factory)

    @staticmethod
    def _k8s_pre_processor_factory(processor_config: dict) -> ProcessorActor:
        """
        Create a Kubernetes pre-processor actor.
        :param processor_config: Resolved Kubernetes pre-processor configuration.
        :return: Configured Kubernetes pre-processor actor.
        """
        from powerapi.processor.pre.k8s.actor import KubernetesPreProcessorActor
        from powerapi.processor.pre.k8s.monitor_agent import KubernetesMonitorConfig

        api_mode = processor_config['api-mode']
        api_host = processor_config.get('api-host')
        api_key = processor_config.get('api-key')
        label_mapping = build_metadata_mapping(processor_config.get('labels', []), prefix='k8s_pod_label_')
        monitor_config = KubernetesMonitorConfig(api_mode, api_host, api_key, label_mapping)

        name = processor_config[ACTOR_NAME_KEY]
        level_logger = logging.DEBUG if processor_config[GENERAL_CONF_VERBOSE_KEY] else logging.INFO
        return KubernetesPreProcessorActor(name, monitor_config, level_logger)

    @staticmethod
    def _openstack_pre_processor_factory(processor_config: dict) -> ProcessorActor:
        """
        Create an OpenStack pre-processor actor.
        :param processor_config: Resolved OpenStack pre-processor configuration.
        :return: Configured OpenStack pre-processor actor.
        """
        from powerapi.processor.pre.openstack.actor import OpenStackPreProcessorActor
        from powerapi.processor.pre.openstack.monitor_agent import (
            OpenStackMonitorConfig,
        )

        api_polling_interval = processor_config['polling-interval']
        metadata_mapping = build_metadata_mapping(processor_config.get('metadata', []), prefix='openstack_metadata_')
        monitor_config = OpenStackMonitorConfig(api_polling_interval, metadata_mapping)

        name = processor_config[ACTOR_NAME_KEY]
        level_logger = logging.DEBUG if processor_config[GENERAL_CONF_VERBOSE_KEY] else logging.INFO
        return OpenStackPreProcessorActor(name, monitor_config, level_logger)
