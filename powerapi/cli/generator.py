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

import os
import sys
from typing import Dict, Tuple, Type

from powerapi.actor import Actor
from powerapi.exception import PowerAPIException
from powerapi.report import HWPCReport, PowerReport, ControlReport, ProcfsReport
from powerapi.database import MongoDB, CsvDB, InfluxDB, OpenTSDB, SocketDB, PrometheusDB, DirectPrometheusDB, VirtioFSDB, FileDB
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor
from powerapi.message import StartMessage, PusherStartMessage, PullerStartMessage
from powerapi.report_modifier.libvirt_mapper import LibvirtMapper


class Generator:
    """
    Generate an actor class and actor start message from config dict
    """

    def __init__(self, component_group_name):
        self.component_group_name = component_group_name

    def generate(self, config: Dict) -> Dict[str, Tuple[Type[Actor], StartMessage]]:
        """
        Generate an actor class and actor start message from config dict
        """
        if self.component_group_name not in config:
            print('Configuration error : no ' + self.component_group_name + ' specified', file=sys.stderr)
            raise PowerAPIException('Configuration error : no ' + self.component_group_name + ' specified')

        actors = {}

        for component_name, component_config in config[self.component_group_name].items():
            try:
                component_type = component_config['type']
                actors[component_name] = self._gen_actor(component_type, component_config, config, component_name)
            except KeyError as exn:
                msg = 'Configuration error : argument ' + exn.args[0]
                msg += ' needed with output ' + component_type
                print(msg, file=sys.stderr)
                raise PowerAPIException(msg) from exn

        return actors

    def _gen_actor(self, component_type: str, component_config: Dict, main_config: Dict, component_name: str) -> Tuple[Type[Actor], StartMessage]:
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
    Exception raised when attempting to add to a DBActorGenerator a database factory with a name already bound to another
    database factory in the DBActorGenerator
    """
    def __init__(self, database_name):
        PowerAPIException.__init__(self)
        self.database_name = database_name


class ModelNameDoesNotExist(PowerAPIException):
    """
    Exception raised when attempting to remove to a DBActorGenerator a model factory with a name that is not bound to another
    model factory in the DBActorGenerator
    """
    def __init__(self, model_name):
        PowerAPIException.__init__(self)
        self.model_name = model_name


class DatabaseNameDoesNotExist(PowerAPIException):
    """
    Exception raised when attempting to remove to a DBActorGenerator a database factory with a name that is not bound to another
    database factory in the DBActorGenerator
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


class DBActorGenerator(Generator):
    """
    ActorGenerator that initialise the start message with a database from config
    """
    def __init__(self, component_group_name):
        Generator.__init__(self, component_group_name)
        self.model_factory = {
            'HWPCReport': HWPCReport,
            'PowerReport': PowerReport,
            'ControlReport': ControlReport,
            'ProcfsReport': ProcfsReport
        }

        self.db_factory = {
            'mongodb': lambda db_config: MongoDB(db_config['model'], db_config['uri'], db_config['db'], db_config['collection']),
            'socket': lambda db_config: SocketDB(db_config['model'], db_config['port']),
            'csv': lambda db_config: CsvDB(db_config['model'], gen_tag_list(db_config),
                                           current_path=os.getcwd() if 'directory' not in db_config else db_config['directory'],
                                           files=[] if 'files' not in db_config else db_config['files']),
            'influxdb': lambda db_config: InfluxDB(db_config['model'], db_config['uri'], db_config['port'], db_config['db'], gen_tag_list(db_config)),
            'opentsdb': lambda db_config: OpenTSDB(db_config['model'], db_config['uri'], db_config['port'], db_config['metric_name']),
            'prom': lambda db_config: PrometheusDB(db_config['model'], db_config['port'], db_config['uri'], db_config['metric_name'],
                                                   db_config['metric_description'], db_config['aggregation_period'], gen_tag_list(db_config)),
            'direct_prom': lambda db_config: DirectPrometheusDB(db_config['model'], db_config['port'], db_config['uri'], db_config['metric_name'],
                                                                db_config['metric_description'], gen_tag_list(db_config)),
            'virtiofs': lambda db_config: VirtioFSDB(db_config['model'], db_config['vm_name_regexp'], db_config['root_directory_name'],
                                                     db_config['vm_directory_name_prefix'], db_config['vm_directory_name_suffix']),
            'filedb': lambda db_config: FileDB(db_config['model'], db_config['filename'])
        }

    def remove_model_factory(self, model_name):
        """
        remove a Model from generator
        """
        if model_name not in self.model_factory:
            raise ModelNameDoesNotExist(model_name)
        del self.model_factory[model_name]

    def remove_db_factory(self, database_name):
        """
        remove a database from generator
        """
        if database_name not in self.db_factory:
            raise DatabaseNameDoesNotExist(database_name)
        del self.db_factory[database_name]

    def add_model_factory(self, model_name, model_factory):
        """
        add a model to generator
        """
        if model_name in self.model_factory:
            raise ModelNameAlreadyUsed(model_name)
        self.model_factory[model_name] = model_factory

    def add_db_factory(self, db_name, db_factory):
        """
        add a database to generator
        """
        if db_name in self.model_factory:
            raise DatabaseNameAlreadyUsed(db_name)
        self.db_factory[db_name] = db_factory

    def _generate_db(self, db_name, db_config, _):
        if db_name not in self.db_factory:
            msg = 'Configuration error : database type ' + db_name + ' unknow'
            print(msg, file=sys.stderr)
            raise PowerAPIException(msg)
        else:
            return self.db_factory[db_name](db_config)

    def _generate_model(self, model_name, db_config):
        if model_name not in self.model_factory:
            msg = 'Configuration error : model type ' + model_name + ' unknow'
            print(msg, file=sys.stderr)
            raise PowerAPIException(msg)
        else:
            return self.model_factory[db_config['model']]

    def _gen_actor(self, db_name, db_config, main_config, actor_name):
        model = self._generate_model(db_config['model'], db_config)
        db_config['model'] = model
        db = self._generate_db(db_name, db_config, main_config)
        start_message = self._start_message_factory(actor_name, db, model, main_config['stream'], main_config['verbose'])
        actor = self._actor_factory(db_config)
        return (actor, start_message)

    def _actor_factory(self, db_config):
        raise NotImplementedError()

    def _start_message_factory(self, name, db, model, stream_mode, level_logger):
        raise NotImplementedError()


class PullerGenerator(DBActorGenerator):
    """
    Generate Puller Actor class and Puller start message from config
    """
    def __init__(self, report_filter, report_modifier_list=[]):
        DBActorGenerator.__init__(self, 'input')
        self.report_filter = report_filter
        self.report_modifier_list = report_modifier_list

    def _actor_factory(self, db_config):
        return PullerActor

    def _start_message_factory(self, name, db, model, stream_mode, level_logger):
        return PullerStartMessage('system', name, db, self.report_filter, stream_mode, report_modifiers=self.report_modifier_list)


class PusherGenerator(DBActorGenerator):
    """
    Generate Pusher actor and Pusher start message from config
    """

    def __init__(self):
        DBActorGenerator.__init__(self, 'output')

    def _actor_factory(self, db_config):
        return PusherActor

    def _start_message_factory(self, name, db, model, stream_mode, level_logger):
        return PusherStartMessage('system', name, db)


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
