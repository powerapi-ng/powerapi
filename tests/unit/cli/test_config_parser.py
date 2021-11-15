# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

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
import pytest

from powerapi.cli.config_parser import ConfigParser, MainConfigParser, SubConfigParser
from powerapi.cli.parser import AlreadyAddedArgumentException, BadTypeException
from powerapi.cli.parser import UnknowArgException, BadContextException, MissingValueException, ComponentAlreadyExistException
from powerapi.cli.parser import SubParserWithoutNameArgumentException, NoNameSpecifiedForComponentException
from powerapi.cli.parser import TooManyArgumentNamesException
from powerapi.cli.parser import store_val, store_true
from powerapi.cli.config_parser import AlreadyAddedSubparserException

###############
# PARSER TEST #
###############
def test_add_argument_that_aldready_exists():
    """
    Add an argument that already exists to a parser and test if an
    AlreadyAddedArgumentException is raised
    """

    parser = MainConfigParser()
    parser.add_argument('a')

    with pytest.raises(AlreadyAddedArgumentException):
        parser.add_argument('a')


#####################
# MAIN PARSER TESTS #
#####################
def test_add_argument_flag():
    """
    Add a short flag to the parser

    Test if the argument was added to the short_arg string
    """
    parser = MainConfigParser()
    assert parser.cli_parser.short_arg == 'h'
    parser.add_argument('a', flag=True)
    assert parser.cli_parser.short_arg == 'ha'


def test_add_argument_2_short():
    """
    Add two short argument (an argument and a flag) to the parser

    Test if the arguments was added to the short_arg string
    """
    parser = MainConfigParser()
    assert parser.cli_parser.short_arg == 'h'
    parser.add_argument('a', flag=True)
    assert parser.cli_parser.short_arg == 'ha'
    parser.add_argument('b')
    assert parser.cli_parser.short_arg == 'hab:'


def test_add_argument_long():
    """
    Add a long argument to the parser

    Test if the argument was added to the long_arg list
    """
    parser = MainConfigParser()
    assert parser.cli_parser.long_arg == ['help']
    parser.add_argument('aaa')
    assert parser.cli_parser.long_arg == ['help', 'aaa=']

def test_add_flag_long():
    """
    Add a long argument to the parser

    Test if the argument was added to the long_arg list
    """
    parser = MainConfigParser()
    assert parser.cli_parser.long_arg == ['help']
    parser.add_argument('aaa', flag=True)
    assert parser.cli_parser.long_arg == ['help', 'aaa']


# full parsing test #
def check_parsing_cli_result(parser, input_str, outputs):

    result = parser._parse_cli(input_str.split())

    assert len(result) == len(outputs)
    assert result == outputs


def test_empty_parser_cli():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknowArgException(z)
    - "-a" : UnknowArgException(a)
    - "-a --sub toto -b" : UnknowArgException(a)
    - "-b" : UnknowArgException(b)

    ConfigParser description :

    - base parser arguments : None
    - subparser toto binded to the argument sub with sub arguments : None
    """
    parser = MainConfigParser()

    check_parsing_cli_result(parser, '', {})

    with pytest.raises(UnknowArgException):
        check_parsing_cli_result(parser, '-z', None)

    with pytest.raises(UnknowArgException):
        check_parsing_cli_result(parser, '-a', None)

    with pytest.raises(UnknowArgException):
        check_parsing_cli_result(parser, '-a --sub toto -b', None)

    with pytest.raises(UnknowArgException):
        check_parsing_cli_result(parser, '-b', None)


def test_empty_parser_validate():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknowArgException(z)
    - "-a" : UnknowArgException(a)
    - "-a --sub toto -b" : UnknowArgException(a)
    - "-b" : UnknowArgException(b)

    ConfigParser description :

    - base parser arguments : None
    - subparser toto binded to the argument sub with sub arguments : None
    """
    parser = MainConfigParser()
    dic = {
        "z": "value"
    }

    with pytest.raises(UnknowArgException):
        parser._validate(dic)


def test_main_parser_cli():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknowArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : UnknowArgException(sub)
    - "-b" : UnknowArgException(b)

    ConfigParser description :

    - base parser arguments : -a
    - subparser toto binded to the argument sub with sub arguments : None
    """
    parser = MainConfigParser()
    parser.add_argument('a', flag=True, action=store_true)

    dic = {
        "z": True
    }

    with pytest.raises(UnknowArgException):
        parser._validate(dic)

    check_parsing_cli_result(parser, '-a', {'a': True})


def test_main_parser_validate():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknowArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : UnknowArgException(sub)
    - "-b" : UnknowArgException(b)

    ConfigParser description :

    - base parser arguments : -a
    - subparser toto binded to the argument sub with sub arguments : None
    """
    parser = MainConfigParser()
    parser.add_argument('a', type=bool, flag=True, action=store_true)

    dic = {
        "z": True
    }

    right_dic = {
        "a": True
    }

    with pytest.raises(UnknowArgException):
        parser._validate(dic)

    assert parser._validate(right_dic) == right_dic


def test_actor_subparser_cli():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknowArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : NoNameSpecifiedForComponentException
    - "-a --sub toto -b --name titi" : {a:True, sub: { titi: { 'type': 'toto', b: True}}}
    - "-b" : BadContextException(b, [toto])

    ConfigParser description :

    - base parser arguments : -a
    - subparser toto binded to the argument sub with sub arguments : -b and --name
    """
    parser = MainConfigParser()
    parser.add_argument('a', flag=True, action=store_true)

    subparser = SubConfigParser('toto')
    subparser.add_argument('b', flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subparser('sub', subparser)


    dic = {
        "z": True
    }

    with pytest.raises(UnknowArgException):
        parser._validate(dic)

    check_parsing_cli_result(parser, '-a', {'a': True})

    with pytest.raises(NoNameSpecifiedForComponentException):
        check_parsing_cli_result(parser, '-a --sub toto -b', {})

    check_parsing_cli_result(parser, '-a --sub toto -b --name titi', {'a': True, 'sub': {'titi': {'type': 'toto', 'b': True}}})

def test_actor_subparser_validate():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknowArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : NoNameSpecifiedForComponentException
    - "-a --sub toto -b --name titi" : {a:True, sub: { titi: { 'type': 'toto', b: True}}}
    - "-b" : BadContextException(b, [toto])

    ConfigParser description :

    - base parser arguments : -a
    - subparser toto binded to the argument sub with sub arguments : -b and --name
    """
    parser = MainConfigParser()
    parser.add_argument('a', type=bool,flag=True, action=store_true)

    subparser = SubConfigParser('toto')
    subparser.add_argument('b', flag=True, action=store_true)
    subparser.add_argument('type', flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subparser('sub', subparser)

    a_dic = {'a': True}

    dic = {
        "z": True
    }

    right_dic = {
        'a': True,
        'sub': {
            'titi':
            {
                'type': 'toto',
                'b': "type"
            }
        }
    }

    with pytest.raises(UnknowArgException):
        parser._validate(dic)

    assert parser._validate(a_dic) == a_dic

    assert parser._validate(right_dic) == right_dic




def test_create_two_component_cli():
    """
    Create two component of the same type with the following cli :
    --sub toto --name titi --sub toto -b --name tutu

    test if the result is :
    {sub:{'titi' : {'type': 'toto'}, 'tutu': {'type': 'toto', 'b':True}}}

    """

    parser = MainConfigParser()
    parser.add_argument('a', flag=True, action=store_true)

    subparser = SubConfigParser('toto')
    subparser.add_argument('b', flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subparser('sub', subparser)

    check_parsing_cli_result(parser, '--sub toto --name titi --sub toto -b --name tutu', {'sub': {'titi': {'type': 'toto'}, 'tutu': {'type': 'toto', 'b': True}}})



def test_create_two_component_validate():
    """
    Create two component of the same type with the following cli :
    --sub toto --name titi --sub toto -b --name tutu

    test if the result is :
    {sub:{'titi' : {'type': 'toto'}, 'tutu': {'type': 'toto', 'b':True}}}

    """

    parser = MainConfigParser()
    parser.add_argument('a', flag=True, action=store_true)

    subparser = SubConfigParser('toto')
    subparser.add_argument('type')
    subparser.add_argument('n', 'name')
    parser.add_subparser('sub', subparser)

    dic = {'sub': {'titi': {'type': 'toto'}, 'tutu': {'type': 'toto', 'b': True}}}
    assert parser._validate(dic) == dic



def test_create_two_with_different_type_component():
    """
    Create two component with different type with the following cli :
    --sub toto --name titi --sub tutu --name tete

    test if the result is :
    {sub:{'titi' : {'type': 'toto'}, 'tete': {'type': 'tutu'}}}

    """
    parser = MainConfigParser()

    subparser = SubConfigParser('toto')
    subparser.add_argument('n', 'name')
    parser.add_subparser('sub', subparser)

    subparser = SubConfigParser('tutu')
    subparser.add_argument('n', 'name')
    parser.add_subparser('sub', subparser)

    check_parsing_cli_result(parser, '--sub toto --name titi --sub tutu --name tete', {'sub': {'titi': {'type': 'toto'}, 'tete': {'type': 'tutu'}}})



def test_create_component_that_already_exist_cli():
    """
    Create two component with the same name with the following cli
    --sub toto --name titi --sub toto --name titi

    test if an ComponentAlreadyExistException is raised
    """
    parser = MainConfigParser()

    subparser = SubConfigParser('toto')
    subparser.add_argument('b', flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subparser('sub', subparser)

    with pytest.raises(ComponentAlreadyExistException):
        check_parsing_cli_result(parser, '--sub toto --name titi --sub toto --name titi', None)


def test_argument_with_val_cli():
    """
    test to parse strings with a parser and retrieve the following results :

    - "-c" : MissingValue(c)
    - "-c 1" : {c : 1}

    ConfigParser description :

    - base parser arguments : -c (not flag)
    """
    parser = MainConfigParser()
    parser.add_argument('c')

    with pytest.raises(MissingValueException):
        check_parsing_cli_result(parser, '-c', None)

    check_parsing_cli_result(parser, '-c 1', {'c': '1'})


def test_argument_with_val_validate():
    """
    test to parse strings with a parser and retrieve the following results :

    - "-c" : MissingValue(c)
    - "-c 1" : {c : 1}

    ConfigParser description :

    - base parser arguments : -c (not flag)
    """
    parser = MainConfigParser()
    parser.add_argument('c')

    dic ={'c': '1'}

    assert parser._validate(dic) == dic



def test_type_cli():
    parser = MainConfigParser()
    parser.add_argument('c', type=int)

    with pytest.raises(BadTypeException):
        check_parsing_cli_result(parser, '-c string', {'c':'string'})

    check_parsing_cli_result(parser, '-c 1', {'c': 1})


def test_type_validate():
    parser = MainConfigParser()
    parser.add_argument('c', type=int)

    str_dic = {'c': 'string'}
    int_dic = {'c': 42}

    with pytest.raises(BadTypeException):
        parser._validate(str_dic)

    assert parser._validate(int_dic) == int_dic

# multi name tests #
def test_short_and_long_name_val():
    """
    Add an argument to a parser with two name long and short and test if the
    value is only bind to the long name in the parsing result

    """
    parser = MainConfigParser()
    parser.add_argument('c', 'coco')

    check_parsing_cli_result(parser, '-c 1', {'coco': '1'})

def test_add_two_short_name():
    """
    Add an argument to a parser with two short name and test if the
    parser raise an exception TooManyArgumentNamesException

    """
    parser = MainConfigParser()
    with pytest.raises(TooManyArgumentNamesException):
        parser.add_argument('c', 'd')


def test_add_two_short_name():
    """
    Add an argument to a parser with two long name and test if the
    parser raise an exception TooManyArgumentNamesException

    """
    parser = MainConfigParser()
    with pytest.raises(TooManyArgumentNamesException):
        parser.add_argument('coco', 'dodo')


# Type tests #
def test_default_type():
    """
    add an argument without specifing the type it must catch. Parse a string
    that contains only this argument and test if the value contained in the
    result is a string

    """
    parser = MainConfigParser()
    parser.add_argument('a')
    result = parser.parse('python -a 1'.split())
    assert len(result) == 1
    assert 'a' in result
    assert isinstance(result['a'], str)


def test_other_type():
    """
    add an argument that must catch an int value, Parse a string that
    contains only this argument and test if the value contained in the result is
    an int

    """
    parser = MainConfigParser()
    parser.add_argument('a', type=int)
    result = parser.parse('python -a 1'.split())
    assert len(result) == 1
    assert 'a' in result
    assert isinstance(result['a'], int)


def test_cant_convert_to_type():
    """
    add an argument that must catch an int value, Parse a string that
    contains only this argument with a value that is not an int test if an
    """
    parser = MainConfigParser()
    parser.add_argument('a', type=int)

    with pytest.raises(BadTypeException):
        parser._parse_cli('-a a'.split())


# parse with Subparser tests #
def test_add_actor_subparser_that_aldready_exists():
    """
    Add a component_subparser that already exists to a parser and test if an
    AlreadyAddedArgumentException is raised
    """
    parser = MainConfigParser()
    subparser = SubConfigParser('titi')
    subparser.add_argument('n', 'name')
    parser.add_subparser('toto', subparser)
    subparser2 = SubConfigParser('titi')
    subparser2.add_argument('n', 'name')

    with pytest.raises(AlreadyAddedSubparserException):
        parser.add_subparser('toto', subparser2)


def test_add_actor_subparser_with_two_name():
    """
    add a component subparser with one short name and one long name
    parse a string and test if the value is only bind to the long name
    """
    parser = MainConfigParser()
    subparser = SubConfigParser('titi')
    subparser.add_argument('a', 'aaa', flag=True, action=store_true, default=False)
    subparser.add_argument('n', 'name')
    parser.add_subparser('sub', subparser)
    check_parsing_cli_result(parser, '--sub titi -a --name tutu', {'sub': {'tutu': {'aaa': True, 'type': 'titi'}}})


def test_add_component_subparser_that_aldready_exists2():
    """
    Add a component_subparser with no argument 'name'
    test if a SubConfigParserWithoutNameArgumentException is raised
    """
    parser = MainConfigParser()
    subparser = SubConfigParser('titi')

    with pytest.raises(SubParserWithoutNameArgumentException):
        parser.add_subparser('toto', subparser)


def test_parse_empty_string_default_value():
    parser = MainConfigParser()
    parser.add_argument('a', default=1)
    result = parser._parse_cli(''.split())
    assert len(result) == 1
    assert 'a' in result
    assert result['a'] == 1


def test_default_validate():
    parser = MainConfigParser()
    parser.add_argument('c', type=int, default=1)

    default_dic = {}
    one_dic = {'c': 1}

    assert parser._validate(default_dic) == one_dic
