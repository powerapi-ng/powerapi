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
from powerapi.cli.parser import MainParser, ComponentSubParser
from powerapi.cli.parser import store_true
from powerapi.cli.parser import BadValueException, MissingValueException
from powerapi.cli.parser import BadTypeException, BadContextException
from powerapi.cli.parser import UnknowArgException
from powerapi.report_model import HWPCModel, PowerModel
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
        subparser_mongo_input.add_argument('d', 'db', help='specify MongoDB database name')
        subparser_mongo_input.add_argument('c', 'collection', help='specify MongoDB database collection')
        subparser_mongo_input.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                           default='hwpc_report')
        self.add_component_subparser('input', subparser_mongo_input,
                                     help_str='specify a database input : --db_output database_name ARG1 ARG2 ... ')

        subparser_csv_input = ComponentSubParser('csv')
        subparser_csv_input.add_argument('f', 'files',
                                         help='specify input csv files with this format : file1,file2,file3',
                                         action=extract_file_names, default=[], check=check_csv_files,
                                         check_msg='one or more csv files couldn\'t be read')
        subparser_csv_input.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                         default='hwpc_report')
        self.add_component_subparser('input', subparser_csv_input,
                                     help_str='specify a database input : --db_output database_name ARG1 ARG2 ... ')
        
        subparser_mongo_output = ComponentSubParser('mongodb')
        subparser_mongo_output.add_argument('u', 'uri', help='sepcify MongoDB uri')
        subparser_mongo_output.add_argument('d', 'db', help='specify MongoDB database name')
        subparser_mongo_output.add_argument('c', 'collection', help='specify MongoDB database collection')
        subparser_mongo_output.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                            default='power_report')
        self.add_component_subparser('output', subparser_mongo_output,
                                     help_str='specify a database output : --db_output database_name ARG1 ARG2 ...')

        subparser_csv_output = ComponentSubParser('csv')
        subparser_csv_output.add_argument('d', 'directory',
                                          help='specify directory where where output  csv files will be writen')
        subparser_csv_output.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                          default='power_report')
        self.add_component_subparser('output', subparser_csv_output,
                                     help_str='specify a database input : --db_output database_name ARG1 ARG2 ... ')

        subparser_influx_output = ComponentSubParser('influxdb')
        subparser_influx_output.add_argument('u', 'uri', help='sepcify InfluxDB uri')
        subparser_influx_output.add_argument('d', 'db', help='specify InfluxDB database name')
        subparser_influx_output.add_argument('p', 'port', help='specify InfluxDB connection port', type=int)
        subparser_influx_output.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                             default='power_report')
        self.add_component_subparser('output', subparser_influx_output,
                                     help_str='specify a database input : --db_output database_name ARG1 ARG2 ... ')

        subparser_opentsdb_output = ComponentSubParser('opentsdb')
        subparser_opentsdb_output.add_argument('u', 'uri', help='sepcify openTSDB host')
        subparser_opentsdb_output.add_argument('p', 'port', help='specify openTSDB connection port', type=int)
        subparser_opentsdb_output.add_argument('metric_name', help='specify metric name')

        subparser_opentsdb_output.add_argument('m', 'model', help='specify data type that will be storen in the database',
                                             default='power_report')
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


DB_FACTORY = {
    'mongodb': lambda db_config: MongoDB(db_config['uri'], db_config['db'], db_config['collection']),
    'csv': lambda db_config: CsvDB(current_path=os.getcwd() if 'directory' not in db_config else db_config['directory'],
                                   files=[] if 'files' not in db_config else db_config['files']),
    'influxdb': lambda db_config: InfluxDB(db_config['uri'], db_config['port'], db_config['db']),
    'opentsdb': lambda db_config: OpenTSDB(db_config['uri'], db_config['port'], db_config['metric_name']),
}


MODEL_FACTORY = {
    'hwpc_report': HWPCModel(),
    'power_report': PowerModel(),
}


def generate_pullers(config, report_filter):
    # default mode if no input are specified
    if 'input' not in config:
        factory = DB_FACTORY['csv']
        model = HWPCModel()
        name = 'csv_puller'
        db_config = {'files': ['core.csv', 'rapl.csv', 'pcu.csv']}
        puller = PullerActor(name, factory(db_config), report_filter, model, stream_mode=config['stream'],
                             level_logger=config['verbose'])
        return {name: puller}

    pullers = {}
    for db_config in config['input']:
        try:
            factory = DB_FACTORY[db_config['type']]
            model = MODEL_FACTORY[db_config['model']]
            name = 'puller_' + db_config['type']
            puller = PullerActor(name, factory(db_config), report_filter, model, stream_mode=config['stream'],
                                 level_logger=config['verbose'])
            pullers[name] = puller
        except KeyError as exn:
            msg = 'CLI error : argument ' + exn.args[0]
            msg += ' needed with --output ' + db_config['type']
            print(msg, file=sys.stderr)
            sys.exit()

    return pullers


def generate_pushers(config):
    # default mode if no output are specified
    if 'output' not in config:
        factory = DB_FACTORY['csv']
        model = PowerModel()
        name = 'csv_pusher'
        pusher = PusherActor(name, model, factory({}), level_logger=config['verbose'])
        return {name: pusher}

    pushers = {}

    for db_config in config['output']:
        try:
            factory = DB_FACTORY[db_config['type']]
            model = MODEL_FACTORY[db_config['model']]
            name = 'pusher_' + db_config['type']
            pusher = PusherActor(name, model, factory(db_config), level_logger=config['verbose'])

            pushers[name] = pusher

        except KeyError as exn:
            msg = 'CLI error : '

            if 'type' not in db_config:
                msg += 'output type not specified'

            else:
                msg += 'argument ' + exn.args[0]
                msg += ' needed with --output ' + db_config['type']
            print(msg, file=sys.stderr)
            sys.exit()

    return pushers
