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

from powerapi.cli.parsing_manager import RootConfigParsingManager, \
    SubgroupConfigParsingManager
from powerapi.exception import AlreadyAddedArgumentException, BadTypeException, UnknownArgException, \
    MissingValueException, SubgroupAlreadyExistException, SubgroupParserWithoutNameArgumentException, \
    NoNameSpecifiedForGroupException, TooManyArgumentNamesException, AlreadyAddedSubparserException
from powerapi.cli.config_parser import store_true


###############
# PARSER TEST #
###############
def test_add_argument_that_already_exists():
    """
    Add an argument that already exists to a parser and test if an
    AlreadyAddedArgumentException is raised
    """

    parser = RootConfigParsingManager()
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
    parser = RootConfigParsingManager()
    assert parser.cli_parser.short_arg == 'h'
    parser.add_argument('a', is_flag=True)
    assert parser.cli_parser.short_arg == 'ha'


def test_add_argument_2_short():
    """
    Add two short argument (an argument and a flag) to the parser

    Test if the arguments was added to the short_arg string
    """
    parser = RootConfigParsingManager()
    assert parser.cli_parser.short_arg == 'h'
    parser.add_argument('a', is_flag=True)
    assert parser.cli_parser.short_arg == 'ha'
    parser.add_argument('b')
    assert parser.cli_parser.short_arg == 'hab:'


def test_add_argument_long():
    """
    Add a long argument to the parser

    Test if the argument was added to the long_arg list
    """
    parser = RootConfigParsingManager()
    assert parser.cli_parser.long_arg == ['help']
    parser.add_argument('aaa')
    assert parser.cli_parser.long_arg == ['help', 'aaa=']


def test_add_flag_long():
    """
    Add a long argument to the parser

    Test if the argument was added to the long_arg list
    """
    parser = RootConfigParsingManager()
    assert parser.cli_parser.long_arg == ['help']
    parser.add_argument('aaa', is_flag=True)
    assert parser.cli_parser.long_arg == ['help', 'aaa']


# full parsing test #
def check_parsing_cli_result(parser, input_str, outputs):
    """
    Check that input_str is correctly parsed by parser
    """
    result = parser._parse_cli(input_str.split())

    assert len(result) == len(outputs)
    assert result == outputs


def test_empty_parser_cli():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : UnknownArgException(a)
    - "-a --sub toto -b" : UnknownArgException(a)
    - "-b" : UnknownArgException(b)

    ConfigParser description :

    - base parser arguments : None
    - subparser toto bound to the argument sub with sub arguments : None
    """
    parser = RootConfigParsingManager()

    check_parsing_cli_result(parser, '', {})

    with pytest.raises(UnknownArgException):
        check_parsing_cli_result(parser, '-z', None)

    with pytest.raises(UnknownArgException):
        check_parsing_cli_result(parser, '-a', None)

    with pytest.raises(UnknownArgException):
        check_parsing_cli_result(parser, '-a --sub toto -b', None)

    with pytest.raises(UnknownArgException):
        check_parsing_cli_result(parser, '-b', None)


def test_empty_parser_validate():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : UnknownArgException(a)
    - "-a --sub toto -b" : UnknownArgException(a)
    - "-b" : UnknownArgException(b)

    ConfigParser description :

    - base parser arguments : None
    - subparser toto bound to the argument sub with sub arguments : None
    """
    parser = RootConfigParsingManager()
    dic = {
        "z": "value"
    }

    with pytest.raises(UnknownArgException):
        parser.validate(dic)


def test_main_parser_cli():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : UnknownArgException(sub)
    - "-b" : UnknownArgException(b)

    ConfigParser description :

    - base parser arguments : -a
    - subparser toto bound to the argument sub with sub arguments : None
    """
    parser = RootConfigParsingManager()
    parser.add_argument('a', is_flag=True, action=store_true)

    dic = {
        "z": True
    }

    with pytest.raises(UnknownArgException):
        parser.validate(dic)

    check_parsing_cli_result(parser, '-a', {'a': True})


def test_main_parser_validate():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : UnknownArgException(sub)
    - "-b" : UnknownArgException(b)

    ConfigParser description :

    - base parser arguments : -a
    - subparser toto bound to the argument sub with sub arguments : None
    """
    parser = RootConfigParsingManager()
    parser.add_argument('a', argument_type=bool, is_flag=True, action=store_true)

    dic = {
        "z": True
    }

    right_dic = {
        "a": True
    }

    with pytest.raises(UnknownArgException):
        parser.validate(dic)

    assert parser.validate(right_dic) == right_dic


def test_actor_subparser_cli():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : NoNameSpecifiedForComponentException
    - "-a --sub toto -b --name titi" : {a:True, sub: { titi: { 'type': 'toto', b: True}}}
    - "-b" : BadContextException(b, [toto])

    ConfigParser description :

    - base parser arguments : -a
    - subparser toto bound to the argument sub with sub arguments : -b and --name
    """
    parser = RootConfigParsingManager()
    parser.add_argument('a', is_flag=True, action=store_true)

    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    dic = {
        "z": True
    }

    with pytest.raises(UnknownArgException):
        parser.validate(dic)

    check_parsing_cli_result(parser, '-a', {'a': True})

    with pytest.raises(NoNameSpecifiedForGroupException):
        check_parsing_cli_result(parser, '-a --sub toto -b', {})

    check_parsing_cli_result(parser, '-a --sub toto -b --name titi',
                             {'a': True, 'sub': {'titi': {'type': 'toto', 'b': True}}})


def test_actor_subparser_validate():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : NoNameSpecifiedForComponentException
    - "-a --sub toto -b --name titi" : {a:True, sub: { titi: { 'type': 'toto', b: True}}}
    - "-b" : BadContextException(b, [toto])

    ConfigParser description :

    - base parser arguments : -a
    - subparser toto bound to the argument sub with sub arguments : -b and --name
    """
    parser = RootConfigParsingManager()
    parser.add_argument('a', argument_type=bool, is_flag=True, action=store_true)

    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('type', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

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

    with pytest.raises(UnknownArgException):
        parser.validate(dic)

    assert parser.validate(a_dic) == a_dic

    assert parser.validate(right_dic) == right_dic


def test_create_two_component_cli():
    """
    Create two component of the same type with the following cli :
    --sub toto --name titi --sub toto -b --name tutu

    test if the result is :
    {sub:{'titi' : {'type': 'toto'}, 'tutu': {'type': 'toto', 'b':True}}}

    """

    parser = RootConfigParsingManager()
    parser.add_argument('a', is_flag=True, action=store_true)

    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    check_parsing_cli_result(parser, '--sub toto --name titi --sub toto -b --name tutu',
                             {'sub': {'titi': {'type': 'toto'}, 'tutu': {'type': 'toto', 'b': True}}})


def test_create_two_component_validate():
    """
    Create two component of the same type with the following cli :
    --sub toto --name titi --sub toto -b --name tutu

    test if the result is :
    {sub:{'titi' : {'type': 'toto'}, 'tutu': {'type': 'toto', 'b':True}}}

    """

    parser = RootConfigParsingManager()
    parser.add_argument('a', is_flag=True, action=store_true)

    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument('type')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    dic = {'sub': {'titi': {'type': 'toto'}, 'tutu': {'type': 'toto', 'b': True}}}
    assert parser.validate(dic) == dic


def test_create_two_with_different_type_component():
    """
    Create two component with different type with the following cli :
    --sub toto --name titi --sub tutu --name tete

    test if the result is :
    {sub:{'titi' : {'type': 'toto'}, 'tete': {'type': 'tutu'}}}

    """
    parser = RootConfigParsingManager()

    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    subparser = SubgroupConfigParsingManager('tutu')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    check_parsing_cli_result(parser, '--sub toto --name titi --sub tutu --name tete',
                             {'sub': {'titi': {'type': 'toto'}, 'tete': {'type': 'tutu'}}})


def test_create_component_that_already_exist_cli():
    """
    Create two component with the same name with the following cli
    --sub toto --name titi --sub toto --name titi

    test if an ComponentAlreadyExistException is raised
    """
    parser = RootConfigParsingManager()

    subparser = SubgroupConfigParsingManager('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    with pytest.raises(SubgroupAlreadyExistException):
        check_parsing_cli_result(parser, '--sub toto --name titi --sub toto --name titi', None)


def test_argument_with_val_cli():
    """
    test to parse strings with a parser and retrieve the following results :

    - "-c" : MissingValue(c)
    - "-c 1" : {c : 1}

    ConfigParser description :

    - base parser arguments : -c (not flag)
    """
    parser = RootConfigParsingManager()
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
    parser = RootConfigParsingManager()
    parser.add_argument('c')

    dic = {'c': '1'}

    assert parser.validate(dic) == dic


def test_type_cli():
    """
        Test that the type of an argument is correctly checked by the parser when a string is used as input
    """
    parser = RootConfigParsingManager()
    parser.add_argument('c', argument_type=int)

    with pytest.raises(BadTypeException):
        check_parsing_cli_result(parser, '-c string', {'c': 'string'})

    check_parsing_cli_result(parser, '-c 1', {'c': 1})


def test_type_validate():
    """
        Test that the type of an argument is correctly validated by the parser when a dict is used as input
    """
    parser = RootConfigParsingManager()
    parser.add_argument('c', argument_type=int)

    str_dic = {'c': 'string'}
    int_dic = {'c': 42}

    with pytest.raises(BadTypeException):
        parser.validate(str_dic)

    assert parser.validate(int_dic) == int_dic


# multi name tests #
def test_short_and_long_name_val():
    """
    Add an argument to a parser with two name long and short and test if the
    value is only bind to the long name in the parsing result

    """
    parser = RootConfigParsingManager()
    parser.add_argument('c', 'coco')

    check_parsing_cli_result(parser, '-c 1', {'coco': '1'})


def test_add_two_short_name():
    """
    Add an argument to a parser with two short name and test if the
    parser raise an exception TooManyArgumentNamesException

    """
    parser = RootConfigParsingManager()
    with pytest.raises(TooManyArgumentNamesException):
        parser.add_argument('c', 'd')


def test_add_two_long_name():
    """
    Add an argument to a parser with two long name and test if the
    parser raise an exception TooManyArgumentNamesException

    """
    parser = RootConfigParsingManager()
    with pytest.raises(TooManyArgumentNamesException):
        parser.add_argument('coco', 'dodo')


# Type tests #
def test_default_type():
    """
    add an argument without specifying the type it must catch. Parse a string
    that contains only this argument and test if the value contained in the
    result is a string

    """
    parser = RootConfigParsingManager()
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
    parser = RootConfigParsingManager()
    parser.add_argument('a', argument_type=int)
    result = parser.parse('python -a 1'.split())
    assert len(result) == 1
    assert 'a' in result
    assert isinstance(result['a'], int)


def test_cant_convert_to_type():
    """
    add an argument that must catch an int value, Parse a string that
    contains only this argument with a value that is not an int test if an
    """
    parser = RootConfigParsingManager()
    parser.add_argument('a', argument_type=int)

    with pytest.raises(BadTypeException):
        parser._parse_cli('-a a'.split())


# parse with Subparser tests #
def test_add_actor_subparser_that_already_exists():
    """
    Add a component_subparser that already exists to a parser and test if an
    AlreadyAddedArgumentException is raised
    """
    parser = RootConfigParsingManager()
    subparser = SubgroupConfigParsingManager('titi')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('toto', subparser)
    subparser2 = SubgroupConfigParsingManager('titi')
    subparser2.add_argument('n', 'name')

    with pytest.raises(AlreadyAddedSubparserException):
        parser.add_subgroup_parser('toto', subparser2)


def test_add_actor_subparser_with_two_name():
    """
    add a component subparser with one short name and one long name
    parse a string and test if the value is only bind to the long name
    """
    parser = RootConfigParsingManager()
    subparser = SubgroupConfigParsingManager('titi')
    subparser.add_argument('a', 'aaa', is_flag=True, action=store_true, default_value=False)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)
    check_parsing_cli_result(parser, '--sub titi -a --name tutu', {'sub': {'tutu': {'aaa': True, 'type': 'titi'}}})


def test_add_component_subparser_that_already_exists2():
    """
    Add a component_subparser with no argument 'name'
    test if a SubConfigParserWithoutNameArgumentException is raised
    """
    parser = RootConfigParsingManager()
    subparser = SubgroupConfigParsingManager('titi')

    with pytest.raises(SubgroupParserWithoutNameArgumentException):
        parser.add_subgroup_parser('toto', subparser)


def test_parse_empty_string_default_value():
    """
        Test that the result of parsing an empty string is a dict of arguments with their default value
    """
    parser = RootConfigParsingManager()
    parser.add_argument('a', default_value=1)
    result = parser._parse_cli(''.split())
    assert len(result) == 1
    assert 'a' in result
    assert result['a'] == 1


def test_default_validate():
    """
        Test that the result of parsing an empty dict is a dict of arguments with their default value
    """
    parser = RootConfigParsingManager()
    parser.add_argument('c', argument_type=int, default_value=1)

    default_dic = {}
    one_dic = {'c': 1}

    assert parser.validate(default_dic) == one_dic
