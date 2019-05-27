"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from powerapi.cli.parser import MainParser, ComponentSubParser
from powerapi.cli.parser import store_true

class CommonCLIParser(MainParser):

    def __init__(self):
        MainParser.__init__(self)

        self.add_argument('v', 'verbose', flag=True, action=store_true, default=False, help='enable verbose mode')
        self.add_argument('s', 'stream', flag=True, action=store_true, default=False, help='enable stream mode')

        subparser_mongo = ComponentSubParser('mongodb')
        subparser_mongo.add_argument('u', 'uri', help='sepcify MongoDB output uri')
        subparser_mongo.add_argument('d', 'db', help='specify MongoDB database name')
        subparser_mongo.add_argument('c', 'collection', help='specify MongoDB database collection')

        self.add_component_subparser('output', subparser_mongo, help_str='specify a database output : --db_output database_name ARG1 ARG2 ...')
        self.add_component_subparser('input', subparser_mongo, help_str='specify a database input : --db_output database_name ARG1 ARG2 ... ')

        
