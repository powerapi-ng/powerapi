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
from powerapi.database import ReadableDatabase, WritableDatabase
from powerapi.exception import PowerAPIException, ModelNameAlreadyUsed, DatabaseNameDoesNotExist, ModelNameDoesNotExist, \
    DatabaseNameAlreadyUsed, ProcessorTypeDoesNotExist, ProcessorTypeAlreadyUsed
from powerapi.filter import ReportFilter
from powerapi.processor.processor_actor import ProcessorActor
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor
from powerapi.report import HWPCReport, PowerReport, Report, FormulaReport

COMPONENT_TYPE_KEY = 'type'
COMPONENT_MODEL_KEY = 'model'
COMPONENT_DB_NAME_KEY = 'db'
COMPONENT_DB_COLLECTION_KEY = 'collection'
COMPONENT_DB_MANAGER_KEY = 'db_manager'
COMPONENT_DB_MAX_BUFFER_SIZE_KEY = 'max_buffer_size'
COMPONENT_URI_KEY = 'uri'

ACTOR_NAME_KEY = 'actor_name'
REGEXP_KEY = 'regexp'

K8S_API_MODE_KEY = 'api-mode'
K8S_API_KEY_KEY = 'api-key'
K8S_API_HOST_KEY = 'api-host'

LISTENER_ACTOR_KEY = 'listener_actor'

GENERAL_CONF_STREAM_MODE_KEY = 'stream'
GENERAL_CONF_VERBOSE_KEY = 'verbose'


class Generator:
    """
    Generate an actor class and actor start message from config dict.
    The config dict has the following structure:
    {
        "arg1_key": value,
        "arg2_key": value
        ...
        "component_group_name1":{
            "arg1_cpn1_key": value,
            "arg2_cpn1_key": value,
            ...

        }
        component_group_name2:{
            ...
        }
        ...
    }
    """

    def __init__(self, component_group_name):
        self.component_group_name = component_group_name

    def generate(self, main_config: dict) -> dict[str, Actor]:
        """
        Generate an actor class and actor start message from config dict
        """
        if self.component_group_name not in main_config:
            raise PowerAPIException(f'Configuration error : Component {self.component_group_name} group is unknown')

        actors = {}
        for component_name, component_config in main_config[self.component_group_name].items():
            try:
                actors[component_name] = self._gen_actor(component_config, main_config, component_name)
            except KeyError as exn:
                raise PowerAPIException(f'Configuration error: Missing "{exn.args[0]}" argument for {component_name} component') from exn
            except ValueError as exn:
                raise PowerAPIException(f'Configuration error: Invalid parameter for {component_name} component: {exn.args[0]}') from exn

        return actors

    def _gen_actor(self, component_config: dict, main_config: dict, component_name: str) -> Actor:
        raise NotImplementedError()


def gen_tag_list(db_config: dict):
    """
    Generate tag list from tag string
    """
    if 'tags' not in db_config or not db_config['tags']:
        return []
    return db_config['tags'].split(',')


class BaseGenerator(Generator):
    """
    Generate an Actor and Start message from config
    """

    def __init__(self, component_group_name: str):
        Generator.__init__(self, component_group_name)
        self.report_classes: dict[str, type[Report]] = {
            'HWPCReport': HWPCReport,
            'PowerReport': PowerReport,
            'FormulaReport': FormulaReport,
        }

    def _gen_actor(self, component_config: dict, main_config: dict, component_name: str):
        model = self._get_report_class(component_config[COMPONENT_MODEL_KEY], component_config)
        component_config[COMPONENT_MODEL_KEY] = model

        actor = self._actor_factory(component_name, main_config, component_config)
        return actor

    def _get_report_class(self, model_name: str, component_config: dict):
        if model_name not in self.report_classes:
            raise PowerAPIException(f'Configuration error: model type {model_name} unknown')

        return self.report_classes[component_config[COMPONENT_MODEL_KEY]]

    def _actor_factory(self, actor_name: str, main_config: dict, component_config: dict):
        raise NotImplementedError


class DBActorGenerator(BaseGenerator):
    """
    ActorGenerator that initialise the start message with a database from config
    """

    def __init__(self, component_group_name: str):
        super().__init__(component_group_name)

        self.db_factory: dict[str, Callable[[dict], ReadableDatabase | WritableDatabase]] = {}

    def remove_report_class(self, model_name: str):
        """
        remove a Model from generator
        """
        if model_name not in self.report_classes:
            raise ModelNameDoesNotExist(model_name)

        del self.report_classes[model_name]

    def remove_db_factory(self, database_name: str):
        """
        remove a database from generator
        """
        if database_name not in self.db_factory:
            raise DatabaseNameDoesNotExist(database_name)

        del self.db_factory[database_name]

    def add_report_class(self, model_name: str, report_class: type[Report]):
        """
        add a report class to generator
        """
        if model_name in self.report_classes:
            raise ModelNameAlreadyUsed(model_name)

        self.report_classes[model_name] = report_class

    def add_db_factory(self, db_name: str, db_factory_function: Callable[[dict], ReadableDatabase | WritableDatabase]):
        """
        add a database to generator
        """
        if db_name in self.db_factory:
            raise DatabaseNameAlreadyUsed(db_name)

        self.db_factory[db_name] = db_factory_function

    def _generate_db(self, db_name: str, component_config: dict):
        try:
            return self.db_factory[db_name](component_config)
        except KeyError as exn:
            raise PowerAPIException('Configuration error: Invalid database type: %s', db_name) from exn
        except ImportError as exn:
            raise PowerAPIException('Dependencies for %s database are not installed', db_name) from exn

    def _gen_actor(self, component_config: dict, main_config: dict, component_name: str):
        model = self._get_report_class(component_config[COMPONENT_MODEL_KEY], component_config)
        component_config[COMPONENT_MODEL_KEY] = model
        database_manager = self._generate_db(component_config[COMPONENT_TYPE_KEY], component_config)
        component_config[COMPONENT_DB_MANAGER_KEY] = database_manager

        actor = self._actor_factory(component_name, main_config, component_config)
        return actor


class PullerGenerator(DBActorGenerator):
    """
    Generate Puller Actor class and Puller start message from config
    """

    @staticmethod
    def _csv_input_database_factory(conf: dict) -> ReadableDatabase:
        """
        CSV Input database factory method.
        """
        from powerapi.database.csv import CSVInput
        return CSVInput(conf['model'], conf['files'])

    @staticmethod
    def _json_input_database_factory(conf: dict) -> ReadableDatabase:
        """
        JSON Input database factory method.
        """
        from powerapi.database.json import JsonInput
        return JsonInput(conf['model'], conf['filepath'], conf['compression'])

    @staticmethod
    def _socket_database_factory(conf: dict) -> ReadableDatabase:
        """
        Socket database factory method.
        """
        from powerapi.database.socket import Socket
        return Socket(conf['model'], conf['host'], conf['port'])

    @staticmethod
    def _mongodb_database_factory(conf: dict) -> ReadableDatabase:
        """
        MongoDB Input database factory method.
        """
        from powerapi.database.mongodb import MongodbInput
        return MongodbInput(conf['model'], conf['uri'], conf['db'], conf['collection'])

    def __init__(self, report_filter: ReportFilter):
        """
        :param report_filter: Report filter to apply for incoming reports
        """
        super().__init__('input')

        self.report_filter = report_filter

        self.add_db_factory('csv', self._csv_input_database_factory)
        self.add_db_factory('json', self._json_input_database_factory)
        self.add_db_factory('socket', self._socket_database_factory)
        self.add_db_factory('mongodb', self._mongodb_database_factory)

    def _actor_factory(self, actor_name: str, main_config, component_config: dict) -> PullerActor:
        """
        Actor factory method.
        :param actor_name: Name of the actor
        :param main_config: Global configuration
        :param component_config: Actor configuration
        :return: Configured Puller actor
        """
        database = component_config[COMPONENT_DB_MANAGER_KEY]
        stream_mode = main_config[GENERAL_CONF_STREAM_MODE_KEY]
        logging_level = logging.DEBUG if main_config[GENERAL_CONF_VERBOSE_KEY] else logging.WARNING
        return PullerActor(actor_name, database, self.report_filter, stream_mode, level_logger=logging_level)


class PusherGenerator(DBActorGenerator):
    """
    Generate Pusher actor and Pusher start message from config
    """

    @staticmethod
    def _csv_output_database_factory(conf: dict) -> WritableDatabase:
        """
        CSV Output database factory method.
        """
        from powerapi.database.csv import CSVOutput
        return CSVOutput(conf['model'], conf['directory'])

    @staticmethod
    def _json_output_database_factory(conf: dict) -> WritableDatabase:
        """
        JSON Output database factory method.
        """
        from powerapi.database.json import JsonOutput
        return JsonOutput(conf['model'], conf['filepath'], conf['compression'])

    @staticmethod
    def _mongodb_database_factory(conf: dict) -> WritableDatabase:
        """
        MongoDB Output database factory method.
        """
        from powerapi.database.mongodb import MongodbOutput
        return MongodbOutput(conf['model'], conf['uri'], conf['db'], conf['collection'])

    @staticmethod
    def _influxdb2_database_factory(conf: dict) -> WritableDatabase:
        """
        InfluxDB2 database factory method.
        """
        from powerapi.database.influxdb2 import InfluxDB2
        return InfluxDB2(conf['model'], conf['uri'], conf['org'], conf['bucket'], conf['token'])

    @staticmethod
    def _opentsdb_database_factory(conf: dict) -> WritableDatabase:
        """
        OpentsDB database factory method.
        """
        from powerapi.database.opentsdb import OpenTSDB
        return OpenTSDB(conf['model'], conf['uri'], conf['port'], conf['metric-name'])

    @staticmethod
    def _prometheus_database_factory(conf: dict) -> WritableDatabase:
        """
        Prometheus database factory method.
        """
        from powerapi.database.prometheus import Prometheus
        return Prometheus(conf['model'], conf['addr'], conf['port'], gen_tag_list(conf))

    def __init__(self):
        super().__init__('output')

        self.add_db_factory('csv', self._csv_output_database_factory)
        self.add_db_factory('json', self._json_output_database_factory)
        self.add_db_factory('mongodb', self._mongodb_database_factory)
        self.add_db_factory('influxdb2', self._influxdb2_database_factory)
        self.add_db_factory('opentsdb', self._opentsdb_database_factory)
        self.add_db_factory('prometheus', self._prometheus_database_factory)

    def _actor_factory(self, actor_name: str, main_config: dict, component_config: dict) -> PusherActor:
        """
        Actor factory method.
        :param actor_name: Name of the actor
        :param main_config: Global configuration
        :param component_config: Actor configuration
        :return: Configured Pusher actor
        """
        database = component_config[COMPONENT_DB_MANAGER_KEY]
        level_logger = logging.DEBUG if main_config[GENERAL_CONF_VERBOSE_KEY] else logging.WARNING
        return PusherActor(actor_name, database, logger_level=level_logger)

    def generate_report_mapping(self, main_config: dict, actors: dict[str, Actor]) -> dict[type[Report], list[ActorProxy]]:
        """
        Generate the report type to pusher actor mapping.
        :param main_config: Main configuration
        :param actors: Dictionary of actors (result of the `generate` method)
        :return: Dictionary mapping the report type to actors that should process it
        """
        if self.component_group_name not in main_config:
            raise PowerAPIException(f'Configuration error: Component "{self.component_group_name}" is not defined')

        report_type_to_actor = {}
        for component_name, component_config in main_config[self.component_group_name].items():
            try:
                actor_proxy = actors[component_name].get_proxy()
                report_type_to_actor.setdefault(component_config[COMPONENT_MODEL_KEY], []).append(actor_proxy)
            except KeyError as exn:
                raise PowerAPIException(f'Actor "{component_name}" is not defined') from exn

        return report_type_to_actor


class ProcessorGenerator(Generator):
    """
    Generator that initializes the processor actor(s) from the configuration.
    """

    def __init__(self, component_group_name: str):
        """
        :param component_group_name: Name of the component group
        """
        super().__init__(component_group_name)

        self.processor_factory: dict[str, Callable[[dict], ProcessorActor]] = {}

    def remove_processor_factory(self, processor_type: str) -> None:
        """
        Remove the given processor actor factory from the generator.
        :param processor_type: Processor type name
        """
        if processor_type not in self.processor_factory:
            raise ProcessorTypeDoesNotExist(processor_type)

        del self.processor_factory[processor_type]

    def add_processor_factory(self, processor_type: str, processor_factory_function: Callable) -> None:
        """
        Add the given processor actor factory to the generator.
        :param processor_type: Processor type name
        :param processor_factory_function: Factory method used to generate the processor actors
        """
        if processor_type in self.processor_factory:
            raise ProcessorTypeAlreadyUsed(processor_type)

        self.processor_factory[processor_type] = processor_factory_function

    def _generate_processor(self, processor_name: str, component_config: dict) -> ProcessorActor:
        try:
            return self.processor_factory[processor_name](component_config)
        except KeyError as exn:
            raise PowerAPIException('Configuration error: Invalid processor type: %s', processor_name) from exn
        except ImportError as exn:
            raise PowerAPIException('Dependencies for %s processor are not installed', processor_name) from exn

    def _gen_actor(self, component_config: dict, main_config: dict, component_name: str) -> ProcessorActor:
        """
        Helper method to generate a processor actor from the given configuration.
        :param component_config: Configuration of the processor component
        :param main_config: Global configuration
        :param component_name: Name of the processor actor to generate
        :return: Processor actor
        """
        processor_actor_type = component_config[COMPONENT_TYPE_KEY]
        component_config[ACTOR_NAME_KEY] = component_name
        component_config[GENERAL_CONF_VERBOSE_KEY] = main_config[GENERAL_CONF_VERBOSE_KEY]
        return self._generate_processor(processor_actor_type, component_config)


class PreProcessorGenerator(ProcessorGenerator):
    """
    Generator that initializes the pre-processor actor(s) from the configuration.
    """

    def __init__(self):
        super().__init__('pre-processor')

        self.add_processor_factory('k8s', self._k8s_pre_processor_factory)
        self.add_processor_factory('openstack', self._openstack_pre_processor_factory)

    @staticmethod
    def _k8s_pre_processor_factory(processor_config: dict) -> ProcessorActor:
        """
        Kubernetes pre-processor actor factory.
        :param processor_config: Pre-Processor configuration
        :return: Configured Kubernetes pre-processor actor
        """
        from powerapi.processor.pre.k8s.actor import K8sPreProcessorActor, K8sProcessorConfig
        name = processor_config[ACTOR_NAME_KEY]
        api_mode = processor_config[K8S_API_MODE_KEY]
        api_host = processor_config.get(K8S_API_HOST_KEY, None)
        api_key = processor_config.get(K8S_API_KEY_KEY, None)
        level_logger = logging.DEBUG if processor_config[GENERAL_CONF_VERBOSE_KEY] else logging.INFO
        config = K8sProcessorConfig(api_mode, api_host, api_key)
        return K8sPreProcessorActor(name, config, level_logger)

    @staticmethod
    def _openstack_pre_processor_factory(processor_config: dict) -> ProcessorActor:
        """
        Openstack pre-processor actor factory.
        :param processor_config: Pre-Processor configuration
        :return: Configured OpenStack pre-processor actor
        """
        from powerapi.processor.pre.openstack.actor import OpenStackPreProcessorActor
        name = processor_config[ACTOR_NAME_KEY]
        api_polling_interval = processor_config['polling-interval']
        level_logger = logging.DEBUG if processor_config[GENERAL_CONF_VERBOSE_KEY] else logging.INFO
        return OpenStackPreProcessorActor(name, api_polling_interval, level_logger)
