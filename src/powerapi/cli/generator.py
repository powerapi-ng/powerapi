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
import os
import sys
from collections.abc import Callable

from powerapi.actor import Actor
from powerapi.database import MongoDB, CsvDB, OpenTSDB, SocketDB, PrometheusDB, VirtioFSDB, FileDB
from powerapi.database.influxdb2 import InfluxDB2
from powerapi.exception import PowerAPIException, ModelNameAlreadyUsed, DatabaseNameDoesNotExist, ModelNameDoesNotExist, \
    DatabaseNameAlreadyUsed, ProcessorTypeDoesNotExist, ProcessorTypeAlreadyUsed
from powerapi.filter import Filter
from powerapi.processor.pre.k8s import K8sPreProcessorActor
from powerapi.processor.processor_actor import ProcessorActor
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor
from powerapi.report import HWPCReport, PowerReport, ControlReport, ProcfsReport, Report, FormulaReport

COMPONENT_TYPE_KEY = 'type'
COMPONENT_MODEL_KEY = 'model'
COMPONENT_DB_NAME_KEY = 'db'
COMPONENT_DB_COLLECTION_KEY = 'collection'
COMPONENT_DB_MANAGER_KEY = 'db_manager'
COMPONENT_DB_MAX_BUFFER_SIZE_KEY = 'max_buffer_size'
COMPONENT_URI_KEY = 'uri'

ACTOR_NAME_KEY = 'actor_name'
TARGET_ACTORS_KEY = 'target_actors'
REGEXP_KEY = 'regexp'

PULLER_NAME_KEY = 'puller'
PUSHER_NAME_KEY = 'pusher'

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

    def generate(self, main_config: dict) -> dict[str, type[Actor]]:
        """
        Generate an actor class and actor start message from config dict
        """
        if self.component_group_name not in main_config:
            raise PowerAPIException('Configuration error : no ' + self.component_group_name + ' specified')

        actors = {}

        for component_name, component_config in main_config[self.component_group_name].items():
            component_type = ''
            try:
                component_type = component_config[COMPONENT_TYPE_KEY]
                actors[component_name] = self._gen_actor(component_config, main_config, component_name)
            except KeyError as exn:
                msg = 'Configuration error : argument ' + exn.args[0]
                msg += ' needed with output ' + component_type
                print(msg, file=sys.stderr)
                raise PowerAPIException(msg) from exn

        return actors

    def _gen_actor(self, component_config: dict, main_config: dict, component_name: str) -> type[Actor]:
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
        self.report_classes = {
            'HWPCReport': HWPCReport,
            'PowerReport': PowerReport
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
        BaseGenerator.__init__(self, component_group_name)
        self.report_classes['FormulaReport'] = FormulaReport
        self.report_classes['ControlReport'] = ControlReport
        self.report_classes['ProcfsReport'] = ProcfsReport

        self.db_factory = {
            'mongodb': lambda db_config: MongoDB(report_type=db_config['model'], uri=db_config['uri'],
                                                 db_name=db_config['db'], collection_name=db_config['collection']),
            'socket': lambda db_config: SocketDB(db_config['model'], db_config['host'], db_config['port']),
            'csv': lambda db_config: CsvDB(report_type=db_config['model'], tags=gen_tag_list(db_config),
                                           current_path=os.getcwd() if 'directory' not in db_config else db_config[
                                               'directory'],
                                           files=[] if 'files' not in db_config else db_config['files']),
            'influxdb2': lambda db_config: InfluxDB2(report_type=db_config['model'], url=db_config['uri'],
                                                     org=db_config['org'],
                                                     bucket_name=db_config['db'], token=db_config['token'],
                                                     tags=gen_tag_list(db_config),
                                                     port=None if 'port' not in db_config else db_config['port']),
            'opentsdb': lambda db_config: OpenTSDB(report_type=db_config['model'], host=db_config['uri'],
                                                   port=db_config['port'], metric_name=db_config['metric-name']),
            'prometheus': lambda db_config: PrometheusDB(report_type=db_config['model'],
                                                         port=db_config['port'],
                                                         address=db_config['uri'],
                                                         metric_name=db_config['metric-name'],
                                                         metric_description=db_config['metric-description'],
                                                         tags=gen_tag_list(db_config)),
            'virtiofs': lambda db_config: VirtioFSDB(report_type=db_config['model'],
                                                     vm_name_regexp=db_config['vm-name-regexp'],
                                                     root_directory_name=db_config['root-directory-name'],
                                                     vm_directory_name_prefix=db_config['vm-directory-name-prefix'],
                                                     vm_directory_name_suffix=db_config['vm-directory-name-suffix']),
            'filedb': lambda db_config: FileDB(report_type=db_config['model'], filename=db_config['filename'])
        }

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

    def add_db_factory(self, db_name: str, db_factory_function):
        """
        add a database to generator
        """
        if db_name in self.db_factory:
            raise DatabaseNameAlreadyUsed(db_name)
        self.db_factory[db_name] = db_factory_function

    def _generate_db(self, db_name: str, component_config: dict):
        if db_name not in self.db_factory:
            msg = 'Configuration error : database type ' + db_name + ' unknown'
            print(msg, file=sys.stderr)
            raise PowerAPIException(msg)

        return self.db_factory[db_name](component_config)

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

    def __init__(self, report_filter: Filter):
        DBActorGenerator.__init__(self, 'input')
        self.report_filter = report_filter

    def _actor_factory(self, actor_name: str, main_config, component_config: dict):
        return PullerActor(name=actor_name, database=component_config[COMPONENT_DB_MANAGER_KEY],
                           report_filter=self.report_filter, stream_mode=main_config[GENERAL_CONF_STREAM_MODE_KEY],
                           report_model=component_config[COMPONENT_MODEL_KEY],
                           level_logger=logging.DEBUG if main_config[GENERAL_CONF_VERBOSE_KEY] else logging.INFO)


class PusherGenerator(DBActorGenerator):
    """
    Generate Pusher actor and Pusher start message from config
    """

    def __init__(self):
        DBActorGenerator.__init__(self, 'output')

    def _actor_factory(self, actor_name: str, main_config: dict, component_config: dict):
        if 'max_buffer_size' in component_config.keys():
            return PusherActor(name=actor_name, report_model=component_config[COMPONENT_MODEL_KEY],
                               database=component_config[COMPONENT_DB_MANAGER_KEY],
                               max_size=component_config[COMPONENT_DB_MAX_BUFFER_SIZE_KEY])

        return PusherActor(name=actor_name, report_model=component_config[COMPONENT_MODEL_KEY],
                           database=component_config[COMPONENT_DB_MANAGER_KEY],
                           level_logger=logging.DEBUG if main_config[GENERAL_CONF_VERBOSE_KEY] else logging.INFO)


class ProcessorGenerator(Generator):
    """
    Generator that initialises the processor from config
    """

    def __init__(self, component_group_name: str, processor_factory: dict[str, Callable[[dict], ProcessorActor]] = None):
        Generator.__init__(self, component_group_name)

        self.processor_factory = processor_factory

    def remove_processor_factory(self, processor_type: str):
        """
        remove a processor from generator
        """
        if processor_type not in self.processor_factory:
            raise ProcessorTypeDoesNotExist(processor_type=processor_type)
        del self.processor_factory[processor_type]

    def add_processor_factory(self, processor_type: str, processor_factory_function: Callable):
        """
        add a processor to generator
        """
        if processor_type in self.processor_factory:
            raise ProcessorTypeAlreadyUsed(processor_type=processor_type)
        self.processor_factory[processor_type] = processor_factory_function

    def _gen_actor(self, component_config: dict, main_config: dict, component_name: str):

        processor_actor_type = component_config[COMPONENT_TYPE_KEY]

        if processor_actor_type not in self.processor_factory:
            msg = 'Configuration error : processor actor type ' + processor_actor_type + ' unknown'
            print(msg, file=sys.stderr)
            raise PowerAPIException(msg)

        component_config[ACTOR_NAME_KEY] = component_name
        component_config[GENERAL_CONF_VERBOSE_KEY] = main_config[GENERAL_CONF_VERBOSE_KEY]
        return self.processor_factory[processor_actor_type](component_config)


class PreProcessorGenerator(ProcessorGenerator):
    """
    Generator that initialises the pre-processor from config.
    """

    def __init__(self):
        super().__init__('pre-processor', self._get_default_processor_factories())

    @staticmethod
    def _k8s_pre_processor_factory(processor_config: dict) -> K8sPreProcessorActor:
        """
        Kubernetes pre-processor actor factory.
        :param processor_config: Pre-Processor configuration
        :return: Configured Kubernetes pre-processor actor
        """
        name = processor_config[ACTOR_NAME_KEY]
        api_mode = processor_config.get(K8S_API_MODE_KEY, 'manual')  # use manual mode by default
        api_host = processor_config.get(K8S_API_HOST_KEY, None)
        api_key = processor_config.get(K8S_API_KEY_KEY, None)
        target_actors_name = [processor_config[PULLER_NAME_KEY]]
        level_logger = logging.DEBUG if processor_config[GENERAL_CONF_VERBOSE_KEY] else logging.INFO
        return K8sPreProcessorActor(name, [], target_actors_name, api_mode, api_host, api_key, level_logger)

    def _get_default_processor_factories(self) -> dict[str, Callable[[dict], ProcessorActor]]:
        """
        Return the default pre-processors factory.
        """
        return {
            'k8s': self._k8s_pre_processor_factory,
        }


class PostProcessorGenerator(ProcessorGenerator):
    """
    Generator that initialises the post-processor from config
    """

    def __init__(self):
        ProcessorGenerator.__init__(self, 'post-processor', self._get_default_processor_factories())

    @staticmethod
    def _get_default_processor_factories() -> dict[str, Callable[[dict], ProcessorActor]]:
        return {}
