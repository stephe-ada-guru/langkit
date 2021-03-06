from os import path

from langkit.compiled_types import (
    ASTNode, Field, Struct, abstract, env_metadata, root_grammar_class
)
from langkit.diagnostics import Diagnostics
from langkit.envs import EnvSpec, add_to_env
from langkit.expressions import Property, Self
from langkit.parsers import Grammar, List, Opt, Row, Tok

from lexer_example import Token
from utils import emit_and_print_errors


Diagnostics.set_lang_source_dir(path.abspath(__file__))


@env_metadata
class Metadata(Struct):
    pass


@root_grammar_class()
class FooNode(ASTNode):
    pass


@abstract
class Stmt(FooNode):
    pass


class Def(Stmt):
    id = Field()
    body = Field()

    name = Property(Self.id)
    env_spec = EnvSpec(
        add_env=True,
        add_to_env=add_to_env(Self.id.symbol, Self)
    )

    faulty_prop = Property(Self._env_value_1)


class Block(Stmt):
    items = Field()

    env_spec = EnvSpec(add_env=True)


def lang_def():
    foo_grammar = Grammar('stmts_rule')
    foo_grammar.add_rules(
        def_rule=Row(
            Tok(Token.Identifier, keep=True),
            Opt(Row('(', foo_grammar.stmts_rule, ')')[1])
        ) ^ Def,

        stmt_rule=(
            foo_grammar.def_rule
            | Row('{',
                  List(foo_grammar.stmt_rule, empty_valid=True),
                  '}') ^ Block
        ),

        stmts_rule=List(foo_grammar.stmt_rule)
    )
    return foo_grammar

emit_and_print_errors(lang_def)
print 'Done'
