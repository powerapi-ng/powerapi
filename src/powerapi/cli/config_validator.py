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

from typing import Dict

from powerapi.exception import MissingArgumentException, NotAllowedArgumentValueException, FileDoesNotExistException, \
    UnexistingActorException


class ConfigValidator:
    """
    Validate powerapi config and initialize missing default values
    """

    @staticmethod
    def validate(config: Dict):
        """
        Validate powerapi config and initialize missing default values
        """
        if 'verbose' not in config:
            config['verbose'] = logging.NOTSET
        if 'stream' not in config:
            config['stream'] = False
        if 'output' not in config:
            logging.error("no output configuration found")
            raise MissingArgumentException(argument_name='output')

        if 'input' not in config:
            logging.error("no input configuration found")
            raise MissingArgumentException(argument_name='input')

        for input_id in config['input']:
            input_config = config['input'][input_id]
            if input_config['type'] == 'csv' \
                    and (
                    'files' not in input_config or input_config['files'] is None or len(input_config['files']) == 0):
                logging.error("no files parameter found for csv input")
                raise MissingArgumentException(argument_name='files')

            if input_config['type'] == 'csv' and config['stream']:
                logging.error("stream mode cannot be used for csv input")
                raise NotAllowedArgumentValueException("Stream mode cannot be used for csv input")

        if 'pre-processor' in config:
            for pre_processor_id in config['pre-processor']:
                pre_processor_config = config['pre-processor'][pre_processor_id]

                if 'puller' not in pre_processor_config:
                    logging.error("no puller name found for pre-processor " + pre_processor_id)
                    raise MissingArgumentException(argument_name='puller')

                puller_id = pre_processor_config['puller']

                if puller_id not in config['input']:
                    logging.error("puller actor " + puller_id + " does not exist")
                    raise UnexistingActorException(actor=puller_id)

        elif 'post-processor' in config:
            for post_processor_id in config['post-processor']:
                post_processor_config = config['post-processor'][post_processor_id]

                if 'pusher' not in post_processor_config:
                    logging.error("no pusher name found for post-processor " + post_processor_id)
                    raise MissingArgumentException(argument_name='pusher')

                pusher_id = post_processor_config['pusher']

                if pusher_id not in config['output']:
                    logging.error("pusher actor " + pusher_id + " does not exist")
                    raise UnexistingActorException(actor=pusher_id)

        ConfigValidator._validate_input(config)

    @staticmethod
    def _validate_input(config: Dict):
        """
        Check that csv input type has files that exist
        """
        for key, input_config in config['input'].items():
            if input_config['type'] == 'csv':
                list_of_files = input_config['files']

                if isinstance(list_of_files, str):
                    list_of_files = input_config['files'].split(",")
                    config['input'][key]['files'] = list_of_files

                for file_name in list_of_files:
                    if not os.access(file_name, os.R_OK):
                        raise FileDoesNotExistException(file_name=file_name)

    @staticmethod
    def _validate_binding(config: Dict):
        """
        Check that defined bindings use existing actors defined by the configuration
        """
        for _, binding_infos in config['binding'].items():

            if 'from' not in binding_infos:
                logging.error("no from parameter found for binding")
                raise MissingArgumentException(argument_name='from')

            if 'to' not in binding_infos:
                logging.error("no to parameter found for binding")
                raise MissingArgumentException(argument_name='to')

            # from_info[0] is the subgroup and from_info[1] the actor name
            from_infos = binding_infos['from'].split('.')

            if from_infos[0] not in config or from_infos[1] not in config[from_infos[0]]:
                logging.error("from actor does not exist")
                raise UnexistingActorException(actor=binding_infos['from'])

            # to_info[0] is the subgroup and to_info[1] the actor name
            to_infos = binding_infos['to'].split('.')

            if to_infos[0] not in config or to_infos[1] not in config[to_infos[0]]:
                logging.error("to actor does not exist")
                raise UnexistingActorException(actor=binding_infos['to'])
