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
from typing import Dict, Type

from powerapi.actor import Actor
from powerapi.database.influxdb2 import InfluxDB2
from powerapi.exception import PowerAPIException
from powerapi.filter import Filter
from powerapi.report import HWPCReport, PowerReport, ControlReport, ProcfsReport, Report, FormulaReport
from powerapi.database import MongoDB, CsvDB, InfluxDB, OpenTSDB, SocketDB, PrometheusDB, DirectPrometheusDB, \
    VirtioFSDB, FileDB
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor

from powerapi.report_modifier.libvirt_mapper import LibvirtMapper
from powerapi.puller.simple.simple_puller_actor import SimplePullerActor
from powerapi.pusher.simple.simple_pusher_actor import SimplePusherActor

COMPONENT_TYPE_KEY = 'type'
COMPONENT_MODEL_KEY = 'model'
COMPONENT_DB_NAME_KEY = 'db'
COMPONENT_DB_COLLECTION_KEY = 'collection'
COMPONENT_DB_MANAGER_KEY = 'db_manager'
COMPONENT_DB_MAX_BUFFER_SIZE = 'max_buffer_size'

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

    def generate(self, main_config: Dict) -> Dict[str, Type[Actor]]:
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

    def _gen_actor(self, component_config: Dict, main_config: Dict, component_name: str) -> Type[Actor]:
        raise NotImplementedError()


class ModelNameAlreadyUsed(PowerAPIException):
    """
    Exception raised when attempting to add to a DBActorGenerator a model factory with a name already bound to another
    model factory in the DBActorGenerator
    """

    def __init__(self, model_name):
        PowerAPIException.__init__(self)
        self.model_name = model_name


class DatabaseNameAlreadyUsed(PowerAPIException):
    """
    Exception raised when attempting to add to a DBActorGenerator a database factory with a name already bound to
    another database factory in the DBActorGenerator
    """

    def __init__(self, database_name):
        PowerAPIException.__init__(self)
        self.database_name = database_name


class ModelNameDoesNotExist(PowerAPIException):
    """
    Exception raised when attempting to remove to a DBActorGenerator a model factory with a name that is not bound to
    another model factory in the DBActorGenerator
    """

    def __init__(self, model_name):
        PowerAPIException.__init__(self)
        self.model_name = model_name


class DatabaseNameDoesNotExist(PowerAPIException):
    """
    Exception raised when attempting to remove to a DBActorGenerator a database factory with a name that is not bound to
    another database factory in the DBActorGenerator
    """

    def __init__(self, database_name):
        PowerAPIException.__init__(self)
        self.database_name = database_name


def gen_tag_list(db_config: Dict):
    """
    Generate tag list from tag string
    """
    if 'tags' not in db_config:
        return []
    return db_config['tags'].split(',')


class SimpleGenerator(Generator):
    """
    Generate Simple Actor class and Simple Start message from config
    """

    def __init__(self, component_group_name: str):
        Generator.__init__(self, component_group_name)
        self.report_classes = {
            'HWPCReport': HWPCReport,
            'PowerReport': PowerReport
        }

    def _gen_actor(self, component_config: Dict, main_config: Dict, component_name: str):
        model = self._get_report_class(component_config[COMPONENT_MODEL_KEY], component_config)
        component_config[COMPONENT_MODEL_KEY] = model

        actor = self._actor_factory(component_name, main_config, component_config)
        return actor

    def _get_report_class(self, model_name, component_config):
        if model_name not in self.report_classes:
            raise PowerAPIException(f'Configuration error: model type {model_name} unknown')

        return self.report_classes[component_config[COMPONENT_MODEL_KEY]]

    def _actor_factory(self, actor_name: str, main_config: Dict, component_config: Dict):
        raise NotImplementedError


class DBActorGenerator(SimpleGenerator):
    """
    ActorGenerator that initialise the start message with a database from config
    """

    def __init__(self, component_group_name: str):
        SimpleGenerator.__init__(self, component_group_name)
        self.report_classes['FormulaReport'] = FormulaReport
        self.report_classes['ControlReport'] = ControlReport
        self.report_classes['ProcfsReport'] = ProcfsReport

        self.db_factory = {
            'mongodb': lambda db_config: MongoDB(db_config['model'], db_config['uri'], db_config['db'],
                                                 db_config['collection']),
            'socket': lambda db_config: SocketDB(db_config['model'], db_config['port']),
            'csv': lambda db_config: CsvDB(db_config['model'], gen_tag_list(db_config),
                                           current_path=os.getcwd() if 'directory' not in db_config else db_config[
                                               'directory'],
                                           files=[] if 'files' not in db_config else db_config['files']),
            'influxdb': lambda db_config: InfluxDB(db_config['model'], db_config['uri'], db_config['port'],
                                                   db_config['db'], gen_tag_list(db_config)),
            'influxdb2': lambda db_config: InfluxDB2(db_config['model'], db_config['uri'], db_config['org'],
                                                     db_config['db'], db_config['token'], gen_tag_list(db_config),
                                                     port=None if 'port' not in db_config else db_config['port']),
            'opentsdb': lambda db_config: OpenTSDB(db_config['model'], db_config['uri'], db_config['port'],
                                                   db_config['metric_name']),
            'prom': lambda db_config: PrometheusDB(db_config['model'], db_config['port'], db_config['uri'],
                                                   db_config['metric_name'],
                                                   db_config['metric_description'], db_config['aggregation_period'],
                                                   gen_tag_list(db_config)),
            'direct_prom': lambda db_config: DirectPrometheusDB(db_config['model'], db_config['port'], db_config['uri'],
                                                                db_config['metric_name'],
                                                                db_config['metric_description'],
                                                                gen_tag_list(db_config)),
            'virtiofs': lambda db_config: VirtioFSDB(db_config['model'], db_config['vm_name_regexp'],
                                                     db_config['root_directory_name'],
                                                     db_config['vm_directory_name_prefix'],
                                                     db_config['vm_directory_name_suffix']),
            'filedb': lambda db_config: FileDB(db_config['model'], db_config['filename'])
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

    def _generate_db(self, db_name: str, component_config: Dict):
        if db_name not in self.db_factory:
            msg = 'Configuration error : database type ' + db_name + ' unknown'
            print(msg, file=sys.stderr)
            raise PowerAPIException(msg)
        else:
            return self.db_factory[db_name](component_config)

    def _gen_actor(self, component_config: Dict, main_config: Dict, actor_name: str):
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

    def __init__(self, report_filter: Filter, report_modifier_list=[]):
        DBActorGenerator.__init__(self, 'input')
        self.report_filter = report_filter
        self.report_modifier_list = report_modifier_list

    def _actor_factory(self, actor_name: str, main_config, component_config: Dict):
        return PullerActor(name=actor_name, database=component_config[COMPONENT_DB_MANAGER_KEY],
                           report_filter=self.report_filter, stream_mode=main_config[GENERAL_CONF_STREAM_MODE_KEY],
                           report_modifier_list=self.report_modifier_list,
                           report_model=component_config[COMPONENT_MODEL_KEY],
                           level_logger=logging.DEBUG if main_config[GENERAL_CONF_VERBOSE_KEY] else logging.INFO)


COMPONENT_NUMBER_OF_REPORTS_TO_SEND_KEY = 'number_of_reports_to_send'


class SimplePullerGenerator(SimpleGenerator):
    """
    Generate Simple Puller Actor class and Simple Puller start message from config
    """

    def __init__(self, report_filter, report_modifier_list=[]):
        SimpleGenerator.__init__(self, 'input')
        self.report_filter = report_filter
        self.report_modifier_list = report_modifier_list

    def _actor_factory(self, actor_name: str, main_config: Dict, component_config: Dict):
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

    def _actor_factory(self, actor_name: str, main_config: Dict, component_config: Dict):
        if 'max_buffer_size' in component_config.keys():
            return PusherActor(name=actor_name, report_model=component_config[COMPONENT_MODEL_KEY],
                               database=component_config[COMPONENT_DB_MANAGER_KEY],
                               max_size=component_config[COMPONENT_DB_MAX_BUFFER_SIZE])

        return PusherActor(name=actor_name, report_model=component_config[COMPONENT_MODEL_KEY],
                           database=component_config[COMPONENT_DB_MANAGER_KEY],
                           level_logger=logging.DEBUG if main_config[GENERAL_CONF_VERBOSE_KEY] else logging.INFO)


class SimplePusherGenerator(SimpleGenerator):
    """
    Generate Simple Pusher actor and Simple Pusher start message from config
    """

    def __init__(self):
        SimpleGenerator.__init__(self, 'output')

    def _actor_factory(self, actor_name: str, main_config: Dict, component_config: Dict):
        return SimplePusherActor(name=actor_name,
                                 number_of_reports_to_store=component_config['number_of_reports_to_store'])


class ReportModifierGenerator:
    """
    Generate Report modifier list from config
    """

    def __init__(self):
        self.factory = {'libvirt_mapper': lambda config: LibvirtMapper(config['uri'], config['domain_regexp'])}

    def generate(self, config: Dict):
        """
        Generate Report modifier list from config
        """
        report_modifier_list = []
        if 'report_modifier' not in config:
            return []
        for report_modifier_name in config['report_modifier'].keys():
            report_modifier = self.factory[report_modifier_name](config['report_modifier'][report_modifier_name])
            report_modifier_list.append(report_modifier)
        return report_modifier_list
