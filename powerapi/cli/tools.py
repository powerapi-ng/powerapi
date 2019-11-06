# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
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
import logging

from functools import reduce
from powerapi.exception import PowerAPIException
from powerapi.cli.parser import MainParser, ComponentSubParser
from powerapi.cli.parser import store_true
from powerapi.cli.parser import BadValueException, MissingValueException
from powerapi.cli.parser import BadTypeException, BadContextException
from powerapi.cli.parser import UnknowArgException
from powerapi.report_model import HWPCModel, PowerModel, FormulaModel
from powerapi.database import MongoDB, CsvDB, InfluxDB, OpenTSDB
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor


def enable_log(arg, val, args, acc):
    acc[arg] = logging.DEBUG
    return args, acc

def check_csv_files(files):
    return reduce(lambda acc, f: acc and os.access(f, os.R_OK), files.split(','), True)


def extract_file_names(arg, val, args, acc):
    acc[arg] = val.split(',')
    return args, acc


class CommonCLIParser(MainParser):

    def __init__(self):
        MainParser.__init__(self)

        self.add_argument('v', 'verbose', flag=True, action=enable_log, default=logging.NOTSET,
                          help='enable verbose mode')
        self.add_argument('s', 'stream', flag=True, action=store_true, default=False, help='enable stream mode')

        subparser_mongo_input = ComponentSubParser('mongodb')
        subparser_mongo_input.add_argument('u', 'uri', help='sepcify MongoDB uri')
        subparser_mongo_input.add_argument('d', 'db', help='specify MongoDB database name', )
        subparser_mongo_input.add_argument('c', 'collection', help='specify MongoDB database collection')
        subparser_mongo_input.add_argument('n', 'name', help='specify puller name', default='puller_mongodb')
        subparser_mongo_input.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                           default='HWPCReport')
        self.add_component_subparser('input', subparser_mongo_input,
                                     help_str='specify a database input : --db_output database_name ARG1 ARG2 ... ')

        subparser_csv_input = ComponentSubParser('csv')
        subparser_csv_input.add_argument('f', 'files',
                                         help='specify input csv files with this format : file1,file2,file3',
                                         action=extract_file_names, default=[], check=check_csv_files,
                                         check_msg='one or more csv files couldn\'t be read')
        subparser_csv_input.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                         default='HWPCReport')
        subparser_csv_input.add_argument('n', 'name', help='specify puller name', default='puller_csv')
        self.add_component_subparser('input', subparser_csv_input,
                                     help_str='specify a database input : --db_output database_name ARG1 ARG2 ... ')

        subparser_mongo_output = ComponentSubParser('mongodb')
        subparser_mongo_output.add_argument('u', 'uri', help='sepcify MongoDB uri')
        subparser_mongo_output.add_argument('d', 'db', help='specify MongoDB database name')
        subparser_mongo_output.add_argument('c', 'collection', help='specify MongoDB database collection')
                                            
        subparser_mongo_output.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                            default='PowerReport')
        subparser_mongo_output.add_argument('n', 'name', help='specify puller name', default='pusher_mongodb')
        self.add_component_subparser('output', subparser_mongo_output,
                                     help_str='specify a database output : --db_output database_name ARG1 ARG2 ...')

        subparser_csv_output = ComponentSubParser('csv')
        subparser_csv_output.add_argument('d', 'directory',
                                          help='specify directory where where output  csv files will be writen')
        subparser_csv_output.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                          default='PowerReport')
        subparser_csv_output.add_argument('n', 'name', help='specify puller name', default='pusher_csv')
        self.add_component_subparser('output', subparser_csv_output,
                                     help_str='specify a database input : --db_output database_name ARG1 ARG2 ... ')

        subparser_influx_output = ComponentSubParser('influxdb')
        subparser_influx_output.add_argument('u', 'uri', help='sepcify InfluxDB uri')
        subparser_influx_output.add_argument('d', 'db', help='specify InfluxDB database name')
        subparser_influx_output.add_argument('p', 'port', help='specify InfluxDB connection port', type=int)
        subparser_influx_output.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                             default='PowerReport')
        subparser_influx_output.add_argument('n', 'name', help='specify puller name', default='pusher_influxdb')
        self.add_component_subparser('output', subparser_influx_output,
                                     help_str='specify a database input : --db_output database_name ARG1 ARG2 ... ')

        subparser_opentsdb_output = ComponentSubParser('opentsdb')
        subparser_opentsdb_output.add_argument('u', 'uri', help='sepcify openTSDB host')
        subparser_opentsdb_output.add_argument('p', 'port', help='specify openTSDB connection port', type=int)
        subparser_opentsdb_output.add_argument('metric_name', help='specify metric name')

        subparser_opentsdb_output.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                             default='PowerReport')
        subparser_opentsdb_output.add_argument('n', 'name', help='specify puller name', default='pusher_opentsdb')
        self.add_component_subparser('output', subparser_opentsdb_output,
                                     help_str='specify a database input : --db_output database_name ARG1 ARG2 ... ')

    def parse_argv(self):
        try:
            return self.parse(sys.argv[1:])

        except BadValueException as exn:
            msg = 'CLI error : argument ' + exn.argument_name + ' : ' + exn.msg
            print(msg, file=sys.stderr)

        except MissingValueException as exn:
            msg = 'CLI error : argument ' + exn.argument_name + ' : expect a value'
            print(msg, file=sys.stderr)

        except BadTypeException as exn:
            msg = 'CLI error : argument ' + exn.argument_name + ' : expect '
            msg += exn.article + ' ' + exn.type_name
            print(msg, file=sys.stderr)

        except UnknowArgException as exn:
            msg = 'CLI error : unknow argument ' + exn.argument_name
            print(msg, file=sys.stderr)

        except BadContextException as exn:
            msg = 'CLI error : argument ' + exn.argument_name
            msg += ' not used in the correct context\nUse it with the following arguments :'
            for main_arg_name, context_name in exn.context_list:
                msg += '\n  --' + main_arg_name + ' ' + context_name
            print(msg, file=sys.stderr)

        sys.exit()


class Generator:

    def __init__(self, component_group_name):
        self.component_group_name = component_group_name

    def generate(self, config):
        if self.component_group_name not in config:
            print('CLI error : no ' + self.component_group_name + ' specified', file=sys.stderr)
            sys.exit()

        actors = {}

        for component_type, components_list in config[self.component_group_name].items():
            for component_name, component_config in components_list.items():
                try:
                    actors[component_name] = self._gen_actor(component_type, component_config, config)
                except KeyError as exn:
                    msg = 'CLI error : argument ' + exn.args[0]
                    msg += ' needed with --output ' + component_type
                    print(msg, file=sys.stderr)
                    sys.exit()

        return actors

    def _gen_actor(self, component_name, component_config, main_config):
        raise NotImplementedError()


class ModelNameAlreadyUsed(PowerAPIException):
    """
    Exception raised when attempting to add to a DBActorGenerator a model factory with a name already bound to another
    model factory in the DBActorGenerator
    """


class ModelNameAlreadyUsed(PowerAPIException):
    """
    Exception raised when attempting to add to a DBActorGenerator a database factory with a name already bound to another
    database factory in the DBActorGenerator
    """


class DBActorGenerator(Generator):

    def __init__(self, component_group_name):
        Generator.__init__(self, component_group_name)
        self.model_factory = {
            'HWPCReport': HWPCModel(),
            'PowerReport': PowerModel(),
            'FormulaReport': FormulaModel(),
        }

        self.db_factory = {
            'mongodb': lambda db_config: MongoDB(db_config['uri'], db_config['db'], db_config['collection']),
            'csv': lambda db_config: CsvDB(current_path=os.getcwd() if 'directory' not in db_config else db_config['directory'],
                                           files=[] if 'files' not in db_config else db_config['files']),
            'influxdb': lambda db_config: InfluxDB(db_config['uri'], db_config['port'], db_config['db']),
            'opentsdb': lambda db_config: OpenTSDB(db_config['uri'], db_config['port'], db_config['metric_name']),
        }

    def add_model_factory(self, model_name, model_factory):
        if model_name in self.model_factory:
            raise ModelNameAlreadyUsed()
        self.model_factory[model_name] = model_factory

    def add_db_factory(self, db_name, db_factory):
        if db_name in self.model_factory:
            raise ModelNameAlreadyUsed()
        self.model_factory[db_name] = db_factory

    def _generate_db(self, db_name, db_config, main_config):
        return self.db_factory[db_name](db_config)


    def _gen_actor(self, db_name, db_config, main_config):
        db = self._generate_db(db_name, db_config, main_config)
        model = self.model_factory[db_config['model']]
        name = db_config['name']
        return self._actor_factory(name, db, model, main_config['stream'], main_config['verbose'])

    def _actor_factory(self, name, db, model, stream_mode, level_logger):
        raise NotImplementedError()


class PullerGenerator(DBActorGenerator):

    def __init__(self, report_filter):
        DBActorGenerator.__init__(self, 'input')
        self.report_filter = report_filter

    def _actor_factory(self, name, db, model, stream_mode, level_logger):
        return PullerActor(name, db, self.report_filter, model, stream_mode, level_logger)


class PusherGenerator(DBActorGenerator):

    def __init__(self):
        DBActorGenerator.__init__(self, 'output')

    def _actor_factory(self, name, db, model, stream_mode, level_logger):
        return PusherActor(name, model, db, level_logger)
