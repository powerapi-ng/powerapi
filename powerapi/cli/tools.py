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

import sys
import logging

from powerapi.cli.parser import MainParser, ComponentSubParser
from powerapi.cli.parser import store_true
from powerapi.cli.parser import BadValueException, MissingValueException
from powerapi.cli.parser import BadTypeException, BadContextException
from powerapi.cli.parser import UnknowArgException
from powerapi.report_model import HWPCModel, PowerModel
from powerapi.database import MongoDB
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor


def enable_log(arg, val, args, acc):
    acc[arg] = logging.DEBUG
    return args, acc


class CommonCLIParser(MainParser):

    def __init__(self):
        MainParser.__init__(self)

        self.add_argument('v', 'verbose', flag=True, action=enable_log,default=logging.NOTSET, help='enable verbose mode')
        self.add_argument('s', 'stream', flag=True, action=store_true, default=False, help='enable stream mode')

        subparser_mongo_input = ComponentSubParser('mongodb')
        subparser_mongo_input.add_argument('u', 'uri', help='sepcify MongoDB uri')
        subparser_mongo_input.add_argument('d', 'db', help='specify MongoDB database name')
        subparser_mongo_input.add_argument('c', 'collection', help='specify MongoDB database collection')
        subparser_mongo_input.add_argument('m', 'model', help='specify data type that will be storen in the database', default='hwpc_report')
        
        subparser_mongo_output = ComponentSubParser('mongodb')
        subparser_mongo_output.add_argument('u', 'uri', help='sepcify MongoDB uri')
        subparser_mongo_output.add_argument('d', 'db', help='specify MongoDB database name')
        subparser_mongo_output.add_argument('c', 'collection', help='specify MongoDB database collection')
        subparser_mongo_output.add_argument('m', 'model', help='specify data type that will be storen in the database', default='power_report')

        self.add_component_subparser('output', subparser_mongo_output, help_str='specify a database output : --db_output database_name ARG1 ARG2 ...')
        self.add_component_subparser('input', subparser_mongo_input, help_str='specify a database input : --db_output database_name ARG1 ARG2 ... ')


    def parse_argv(self):
        try:
            return self.parse(sys.argv[1:])

        except BadValueException as exn:
            msg = 'CLI error : argument ' + exn.argument_name + ' ' + exn.msg
            print(msg, file=sys.stderr)
        except MissingValueException as exn:
            msg = 'CLI error : argument ' + exn.argument_name + ' expect a value'
            print(msg, file=sys.stderr)
        except BadTypeException as exn:
            msg = 'CLI error : argument ' + exn.argument_name + ' expect '
            msg += exn.article + ' ' + exn.type_name
            print(msg, file=sys.stderr)
        except UnknowArgException as exn:
            msg = 'CLI error : unknow argument ' + exn.argument_name
            print(msg, file=sys.stderr)
        except BadContextException as exn:
            msg = 'CLI error : argument ' + exn.argument_name
            msg += 'not used in the correct context\nUse it with the following arguments :'
            for main_arg_name, context_name in exn.context_list:
                msg += '\n  --' + main_arg_name + ' ' + context_name
            print(msg, file=sys.stderr)
        sys.exit()


DB_FACTORY = {
    'mongodb': lambda db_config: MongoDB(db_config['uri'], db_config['db'], db_config['collection']),
}


MODEL_FACTORY = {
    'hwpc_report': HWPCModel(),
    'power_report': PowerModel(),
}


def generate_pullers(config, report_filter):

    pullers = {}

    for db_config in config['input']:
        try:
            factory = DB_FACTORY[db_config['type']]
            model = MODEL_FACTORY[db_config['model']]
            name = 'puller_' + db_config['type']
            puller = PullerActor(name, factory(db_config), report_filter, model,
                                 stream_mode=config['stream'],
                                 level_logger=config['verbose'])
            pullers[name] = puller
        except KeyError as exn:
            msg = 'CLI error : argument ' + exn.args[0]
            msg += ' needed with --output ' + db_config['type']
            print(msg, file=sys.stderr)
            sys.exit()

    return pullers


def generate_pushers(config):
    pushers = {}

    for db_config in config['output']:
        try:
            factory = DB_FACTORY[db_config['type']]
            model = MODEL_FACTORY[db_config['model']]
            name = 'pusher_' + db_config['type']
            pusher = PusherActor(name, model, factory(db_config),
                                 level_logger=config['verbose'])

            pushers[name] = pusher

        except KeyError as exn:
            msg = 'CLI error : argument ' + exn.args[0]
            msg += ' needed with --output ' + db_config['type']
            print(msg, file=sys.stderr)
            sys.exit()

    return pushers
