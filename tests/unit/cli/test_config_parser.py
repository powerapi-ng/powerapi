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

from powerapi.cli.config_parser import BaseConfigParser, RootConfigParser, SubgroupConfigParser
from powerapi.cli.config_parser import store_true
from powerapi.exception import AlreadyAddedArgumentException, BadTypeException, UnknownArgException, \
    BadContextException, MissingValueException, SubgroupAlreadyExistException, SubgroupParserWithoutNameArgumentException, \
    NoNameSpecifiedForGroupException, TooManyArgumentNamesException


###############
# PARSER TEST #
###############
def test_add_argument_that_already_exists():
    """
    Add an argument that already exists to a BaseParser and test if an
    AlreadyAddedArgumentException is raised
    """

    parser = BaseConfigParser()
    parser.add_argument('a')

    with pytest.raises(AlreadyAddedArgumentException):
        parser.add_argument('a')


#####################
# MAIN PARSER TESTS #
#####################
# Test add_argument optargs #
def test_add_argument_short():
    """
    Add a short argument to the parser

    Test if the argument was added to the short_arg string
    """
    parser = RootConfigParser(help_arg=False)
    assert parser.short_arg == ''
    parser.add_argument('a')
    assert parser.short_arg == 'a:'


def test_add_argument_flag():
    """
    Add a short flag to the parser

    Test if the argument was added to the short_arg string
    """
    parser = RootConfigParser(help_arg=False)
    assert parser.short_arg == ''
    parser.add_argument('a', is_flag=True)
    assert parser.short_arg == 'a'


def test_add_argument_2_short():
    """
    Add two short argument (an argument and a flag) to the parser

    Test if the arguments was added to the short_arg string
    """
    parser = RootConfigParser(help_arg=False)
    assert parser.short_arg == ''
    parser.add_argument('a', is_flag=True)
    assert parser.short_arg == 'a'
    parser.add_argument('b')
    assert parser.short_arg == 'ab:'


def test_add_argument_long():
    """
    Add a long argument to the parser

    Test if the argument was added to the long_arg list
    """
    parser = RootConfigParser(help_arg=False)
    assert not parser.long_arg
    parser.add_argument('aaa')
    assert parser.long_arg == ['aaa=']


def test_add_flag_long():
    """
    Add a long argument to the parser

    Test if the argument was added to the long_arg list
    """
    parser = RootConfigParser(help_arg=False)
    assert not parser.long_arg
    parser.add_argument('aaa', is_flag=True)
    assert parser.long_arg == ['aaa']


# full parsing test #
def check_parsing_result(parser, input_str, outputs):
    """
    Check that input_str is correctly parsed by parser
    """
    result = parser.parse(input_str.split())

    assert len(result) == len(outputs)
    assert result == outputs


def test_empty_parser():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : UnknownArgException(a)
    - "-a --sub toto -b" : UnknownArgException(a)
    - "-b" : UnknownArgException(b)

    Parser description :

    - base parser arguments : None
    - subparser toto bound to the argument sub with sub arguments : None
    """
    parser = RootConfigParser(help_arg=False)

    check_parsing_result(parser, '', {})

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-z', None)

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-a', None)

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-a --sub toto -b', None)

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-b', None)


def test_main_parser():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : UnknownArgException(sub)
    - "-b" : UnknownArgException(b)

    Parser description :

    - base parser arguments : -a
    - subparser toto bound to the argument sub with sub arguments : None
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', is_flag=True, action=store_true)

    check_parsing_result(parser, '', {})

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-z', None)

    check_parsing_result(parser, '-a', {'a': True})

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-a --sub toto -b', None)

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-b', None)


def test_actor_subparser():
    """
    test to parse strings with a parser and retrieve the following results :

    - "" : {}
    - "-z" : UnknownArgException(z)
    - "-a" : {a: True}
    - "-a --sub toto -b" : NoNameSpecifiedForComponentException
    - "-a --sub toto -b --name titi" : {a:True, sub: { titi: { 'type': 'toto', b: True}}}
    - "-b" : BadContextException(b, [toto])

    Parser description :

    - base parser arguments : -a
    - subparser toto bound to the argument sub with sub arguments : -b and --name
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', is_flag=True, action=store_true)

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    check_parsing_result(parser, '', {})

    with pytest.raises(UnknownArgException):
        check_parsing_result(parser, '-z', None)

    check_parsing_result(parser, '-a', {'a': True})

    with pytest.raises(NoNameSpecifiedForGroupException):
        check_parsing_result(parser, '-a --sub toto -b', {})

    check_parsing_result(parser, '-a --sub toto -b --name titi',
                         {'a': True, 'sub': {'titi': {'type': 'toto', 'b': True}}})

    with pytest.raises(BadContextException):
        check_parsing_result(parser, '-b', None)


def test_create_two_component():
    """
    Create two component of the same type with the following cli :
    --sub toto --name titi --sub toto -b --name tutu

    test if the result is :
    {sub:{'titi' : {'type': 'toto'}, 'tutu': {'type': 'toto', 'b':True}}}

    """
    parser = RootConfigParser(help_arg=False)

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    check_parsing_result(parser, '--sub toto --name titi --sub toto -b --name tutu',
                         {'sub': {'titi': {'type': 'toto'}, 'tutu': {'type': 'toto', 'b': True}}})


def test_create_two_with_different_type_component():
    """
    Create two component with different type with the following cli :
    --sub toto --name titi --sub tutu --name tete

    test if the result is :
    {sub:{'titi' : {'type': 'toto'}, 'tete': {'type': 'tutu'}}}

    """
    parser = RootConfigParser(help_arg=False)

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    subparser = SubgroupConfigParser('tutu')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    check_parsing_result(parser, '--sub toto --name titi --sub tutu --name tete',
                         {'sub': {'titi': {'type': 'toto'}, 'tete': {'type': 'tutu'}}})


def test_create_component_that_already_exist():
    """
    Create two component with the same name with the following cli
    --sub toto --name titi --sub toto --name titi

    test if an ComponentAlreadyExistException is raised
    """
    parser = RootConfigParser(help_arg=False)

    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('b', is_flag=True, action=store_true)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)

    with pytest.raises(SubgroupAlreadyExistException):
        check_parsing_result(parser, '--sub toto --name titi --sub toto --name titi', None)


def test_argument_with_val():
    """
    test to parse strings with a parser and retrieve the following results :

    - "-c" : MissingValue(c)
    - "-c 1" : {c : 1}

    Parser description :

    - base parser arguments : -c (not flag)
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('c')

    with pytest.raises(MissingValueException):
        check_parsing_result(parser, '-c', None)

    check_parsing_result(parser, '-c 1', {'c': '1'})


# multi name tests #
def test_short_and_long_name_val():
    """
    Add an argument to a parser with two name long and short and test if the
    value is only bind to the long name in the parsing result

    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('c', 'coco')

    check_parsing_result(parser, '-c 1', {'coco': '1'})


def test_add_two_short_name():
    """
    Add an argument to a parser with two short name and test if the
    parser raise an exception TooManyArgumentNamesException

    """
    parser = RootConfigParser(help_arg=False)
    with pytest.raises(TooManyArgumentNamesException):
        parser.add_argument('c', 'd')


def test_add_two_long_name():
    """
    Add an argument to a parser with two long name and test if the
    parser raise an exception TooManyArgumentNamesException

    """
    parser = RootConfigParser(help_arg=False)
    with pytest.raises(TooManyArgumentNamesException):
        parser.add_argument('coco', 'dodo')


# Type tests #
def test_default_type():
    """
    add an argument without specifying the type it must catch. Parse a string
    that contains only this argument and test if the value contained in the
    result is a string

    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a')
    result = parser.parse('-a 1'.split())
    assert len(result) == 1
    assert 'a' in result
    assert isinstance(result['a'], str)


def test_other_type():
    """
    add an argument that must catch an int value, Parse a string that
    contains only this argument and test if the value contained in the result is
    an int

    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', argument_type=int)
    result = parser.parse('-a 1'.split())
    assert len(result) == 1
    assert 'a' in result
    assert isinstance(result['a'], int)


def test_cant_convert_to_type():
    """
    add an argument that must catch an int value, Parse a string that
    contains only this argument with a value that is not an int test if an
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', argument_type=int)

    with pytest.raises(BadTypeException):
        parser.parse('-a a'.split())


# parse with ComponentSubparser tests #
def test_add_actor_subparser_that_already_exists():
    """
    Add a component_subparser that already exists to a parser and test if an
    AlreadyAddedArgumentException is raised
    """
    parser = RootConfigParser(help_arg=False)
    subparser = SubgroupConfigParser('titi')
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('toto', subparser)
    subparser2 = SubgroupConfigParser('titi')
    subparser2.add_argument('n', 'name')

    with pytest.raises(AlreadyAddedArgumentException):
        parser.add_subgroup_parser('toto', subparser2)


def test_add_actor_subparser_with_two_name():
    """
    add a component subparser with one short name and one long name
    parse a string and test if the value is only bind to the long name
    """
    parser = RootConfigParser(help_arg=False)
    subparser = SubgroupConfigParser('titi')
    subparser.add_argument('a', 'aaa', is_flag=True, action=store_true, default_value=False)
    subparser.add_argument('n', 'name')
    parser.add_subgroup_parser('sub', subparser)
    check_parsing_result(parser, '--sub titi -a --name tutu', {'sub': {'tutu': {'aaa': True, 'type': 'titi'}}})


def test_add_component_subparser_that_already_exists2():
    """
    Add a component_subparser with no argument 'name'
    test if a SubParserWithoutNameArgumentException is raised
    """
    parser = RootConfigParser(help_arg=False)
    subparser = SubgroupConfigParser('titi')

    with pytest.raises(SubgroupParserWithoutNameArgumentException):
        parser.add_subgroup_parser('toto', subparser)


def test_parse_empty_string_default_value():
    """
    Test that the result of parsing an empty string is a dict of arguments with their default value
    """
    parser = RootConfigParser(help_arg=False)
    parser.add_argument('a', default_value=1)
    result = parser.parse(''.split())
    assert len(result) == 1
    assert 'a' in result
    assert result['a'] == 1


############################
# COMPONENT_SUBPARSER TEST #
############################
def test_component_subparser_empty(subgroup_parser):
    """
    Test component_subparser, parse an empty token list.
    Must return an empty dictionary as parse result and an empty token
    list
    """
    assert subgroup_parser.parse([]) == ([], {})


def test_component_subparser_normal_token_list(subgroup_parser):
    """
    test component_subparser, parse a token list which contain only subparser
    argument [('a', '')].

    must return return a  dictionary {'a':''} as parse result
    and an empty token list

    """
    assert subgroup_parser.parse([('a', '')]) == ([], {'a': None})


def test_component_subparser_full_token_list(subgroup_parser):
    """
    test component_subparser, parse a token list which contain subparser
    argument and arguments from other parser[('a', ''), ('b', '')].

    must return return a  dictionary {'a':''} as parse result
    and a token list that contains the unparsed arguments : [('b', '')].

    """
    assert subgroup_parser.parse([('a', ''), ('b', '')]) == ([('b', '')],
                                                             {'a': None})


def test_subparser_empty_token_list_default_value():
    """
    Test that the result of parsing an empty string is a dict of arguments with their default value
    """
    subparser = SubgroupConfigParser('toto')
    subparser.add_argument('a', default_value=1)
    acc, result = subparser.parse([])
    assert len(result) == 1
    assert 'a' in result
    assert result['a'] == 1
    assert acc == []
