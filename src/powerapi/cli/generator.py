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
from typing import Dict, Type, Callable

from powerapi.actor import Actor
from powerapi.database.influxdb2 import InfluxDB2
from powerapi.exception import PowerAPIException, ModelNameAlreadyUsed, DatabaseNameDoesNotExist, ModelNameDoesNotExist, \
    DatabaseNameAlreadyUsed, ProcessorTypeDoesNotExist, ProcessorTypeAlreadyUsed, MonitorTypeDoesNotExist
from powerapi.filter import Filter
from powerapi.processor.pre.k8s.k8s_monitor import K8sMonitorAgent
from powerapi.processor.pre.k8s.k8s_pre_processor_actor import K8sPreProcessorActor, TIME_INTERVAL_DEFAULT_VALUE, \
    TIMEOUT_QUERY_DEFAULT_VALUE
from powerapi.processor.pre.libvirt.libvirt_pre_processor_actor import LibvirtPreProcessorActor
from powerapi.report import HWPCReport, PowerReport, ControlReport, ProcfsReport, Report, FormulaReport
from powerapi.database import MongoDB, CsvDB, OpenTSDB, SocketDB, PrometheusDB, \
    VirtioFSDB, FileDB
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor

from powerapi.puller.simple.simple_puller_actor import SimplePullerActor
from powerapi.pusher.simple.simple_pusher_actor import SimplePusherActor

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
K8S_API_MODE_KEY = 'k8s-api-mode'
TIME_INTERVAL_KEY = 'time-interval'
TIMEOUT_QUERY_KEY = 'timeout-query'
PULLER_NAME_KEY = 'puller'
PUSHER_NAME_KEY = 'pusher'
API_KEY_KEY = 'api-key'
HOST_KEY = 'host'

LISTENER_ACTOR_KEY = 'listener_actor'

GENERAL_CONF_STREAM_MODE_KEY = 'stream'
GENERAL_CONF_VERBOSE_KEY = 'verbose'

MONITOR_NAME_SUFFIX = '_monitor'
MONITOR_KEY = 'monitor'
K8S_COMPONENT_TYPE_VALUE = 'k8s'


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

    def generate(self, main_config: dict) -> Dict[str, Type[Actor]]:
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

    def _gen_actor(self, component_config: dict, main_config: dict, component_name: str) -> Type[Actor]:
        raise NotImplementedError()


def gen_tag_list(db_config: dict):
    """
    Generate tag list from tag string
    """
    if 'tags' not in db_config:
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
            'socket': lambda db_config: SocketDB(report_type=db_config['model'], port=db_config['port']),
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
                                                   port=db_config['port'], metric_name=db_config['metric_name']),
            'prometheus': lambda db_config: PrometheusDB(report_type=db_config['model'],
                                                         port=db_config['port'],
                                                         address=db_config['uri'],
                                                         metric_name=db_config['metric_name'],
                                                         metric_description=db_config['metric_description'],
                                                         tags=gen_tag_list(db_config)),
            'virtiofs': lambda db_config: VirtioFSDB(report_type=db_config['model'],
                                                     vm_name_regexp=db_config['vm_name_regexp'],
                                                     root_directory_name=db_config['root_directory_name'],
                                                     vm_directory_name_prefix=db_config['vm_directory_name_prefix'],
                                                     vm_directory_name_suffix=db_config['vm_directory_name_suffix']),
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

    def add_report_class(self, model_name: str, report_class: Type[Report]):
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
        else:
            return self.db_factory[db_name](component_config)

    def _gen_actor(self, component_config: dict, main_config: dict, actor_name: str):
        model = self._get_report_class(component_config[COMPONENT_MODEL_KEY], component_config)
        component_config[COMPONENT_MODEL_KEY] = model
        database_manager = self._generate_db(component_config[COMPONENT_TYPE_KEY], component_config)
        component_config[COMPONENT_DB_MANAGER_KEY] = database_manager

        actor = self._actor_factory(actor_name, main_config, component_config)
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


COMPONENT_NUMBER_OF_REPORTS_TO_SEND_KEY = 'number_of_reports_to_send'


class SimplePullerGenerator(BaseGenerator):
    """
    Generate Simple Puller Actor class and Simple Puller start message from config
    """

    def __init__(self, report_filter, report_modifier_list=None):
        BaseGenerator.__init__(self, 'input')
        self.report_filter = report_filter

        if report_modifier_list is None:
            report_modifier_list = []
        self.report_modifier_list = report_modifier_list

    def _actor_factory(self, actor_name: str, main_config: dict, component_config: dict):
        return SimplePullerActor(name=actor_name, report_filter=self.report_filter,
                                 number_of_reports_to_send=component_config[COMPONENT_NUMBER_OF_REPORTS_TO_SEND_KEY],
                                 report_type_to_send=component_config[COMPONENT_MODEL_KEY])


COMPONENT_NUMBER_OF_REPORTS_TO_STORE_KEY = 'number_of_reports_to_store'


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


class SimplePusherGenerator(BaseGenerator):
    """
    Generate Simple Pusher actor and Simple Pusher start message from config
    """

    def __init__(self):
        BaseGenerator.__init__(self, 'output')

    def _actor_factory(self, actor_name: str, main_config: dict, component_config: dict):
        return SimplePusherActor(name=actor_name,
                                 number_of_reports_to_store=component_config['number_of_reports_to_store'])


class ProcessorGenerator(Generator):
    """
    Generator that initialises the processor from config
    """

    def __init__(self, component_group_name: str):
        Generator.__init__(self, component_group_name=component_group_name)

        self.processor_factory = self._get_default_processor_factories()

    def _get_default_processor_factories(self) -> dict:
        """
        Init the factories for this processor generator
        """
        raise NotImplementedError

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

    def _gen_actor(self, component_config: dict, main_config: dict, actor_name: str):

        processor_actor_type = component_config[COMPONENT_TYPE_KEY]

        if processor_actor_type not in self.processor_factory:
            msg = 'Configuration error : processor actor type ' + processor_actor_type + ' unknown'
            print(msg, file=sys.stderr)
            raise PowerAPIException(msg)
        else:
            component_config[ACTOR_NAME_KEY] = actor_name
            component_config[GENERAL_CONF_VERBOSE_KEY] = main_config[GENERAL_CONF_VERBOSE_KEY]
            return self.processor_factory[processor_actor_type](component_config)


class PreProcessorGenerator(ProcessorGenerator):
    """
    Generator that initialises the pre-processor from config
    """

    def __init__(self):
        ProcessorGenerator.__init__(self, component_group_name='pre-processor')

    def _get_default_processor_factories(self) -> dict:
        return {
            'libvirt': lambda processor_config: LibvirtPreProcessorActor(name=processor_config[ACTOR_NAME_KEY],
                                                                         uri=processor_config[COMPONENT_URI_KEY],
                                                                         regexp=processor_config[REGEXP_KEY],
                                                                         target_actors_names=[processor_config
                                                                                              [PULLER_NAME_KEY]]),
            'k8s': lambda processor_config: K8sPreProcessorActor(name=processor_config[ACTOR_NAME_KEY],
                                                                 ks8_api_mode=None if
                                                                 K8S_API_MODE_KEY not in processor_config else
                                                                 processor_config[K8S_API_MODE_KEY],
                                                                 time_interval=TIME_INTERVAL_DEFAULT_VALUE if
                                                                 TIME_INTERVAL_KEY not in processor_config else
                                                                 processor_config[TIME_INTERVAL_KEY],
                                                                 timeout_query=TIMEOUT_QUERY_DEFAULT_VALUE if
                                                                 TIMEOUT_QUERY_KEY not in processor_config
                                                                 else processor_config[TIMEOUT_QUERY_KEY],
                                                                 api_key=None if API_KEY_KEY not in processor_config
                                                                 else processor_config[API_KEY_KEY],
                                                                 host=None if HOST_KEY not in processor_config
                                                                 else processor_config[HOST_KEY],
                                                                 level_logger=logging.DEBUG if
                                                                 processor_config[GENERAL_CONF_VERBOSE_KEY] else
                                                                 logging.INFO,
                                                                 target_actors_names=[processor_config[PULLER_NAME_KEY]]
                                                                 )
        }


class PostProcessorGenerator(ProcessorGenerator):
    """
    Generator that initialises the post-processor from config
    """

    def __init__(self):
        ProcessorGenerator.__init__(self, component_group_name='post-processor')

    def _get_default_processor_factories(self) -> dict:
        return {}


class MonitorGenerator(Generator):
    """
    Generator that initialises the monitor by using a K8sPreProcessorActor
    """

    def __init__(self):
        Generator.__init__(self, component_group_name=MONITOR_KEY)

        self.monitor_factory = {
            K8S_COMPONENT_TYPE_VALUE: lambda monitor_config: K8sMonitorAgent(
                name=monitor_config[ACTOR_NAME_KEY],
                concerned_actor_state=monitor_config[LISTENER_ACTOR_KEY].state,
                level_logger=monitor_config[LISTENER_ACTOR_KEY].logger.getEffectiveLevel()
            )

        }

    def _gen_actor(self, component_config: dict, main_config: dict, actor_name: str):

        monitor_actor_type = component_config[COMPONENT_TYPE_KEY]

        if monitor_actor_type not in self.monitor_factory:
            raise MonitorTypeDoesNotExist(monitor_type=monitor_actor_type)
        else:
            component_config[ACTOR_NAME_KEY] = actor_name + MONITOR_NAME_SUFFIX
            return self.monitor_factory[monitor_actor_type](component_config)

    def generate_from_processors(self, processors: dict) -> dict:
        """
        Generates monitors associated with the given processors
        :param dict processors: Dictionary with the processors for the generation
        """

        monitors_config = {MONITOR_KEY: {}}

        for processor_name, processor in processors.items():

            if isinstance(processor, K8sPreProcessorActor):
                monitors_config[MONITOR_KEY][processor_name + MONITOR_NAME_SUFFIX] = {
                    COMPONENT_TYPE_KEY: K8S_COMPONENT_TYPE_VALUE,
                    LISTENER_ACTOR_KEY: processor}

        return self.generate(main_config=monitors_config)
