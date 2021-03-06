from langkit.compiled_types import (
    ASTNode, root_grammar_class, LongType, Field, Struct
)
from langkit.diagnostics import Diagnostics
from langkit.expressions import Property, New, Literal, No
from langkit.parsers import Grammar, Row

from os import path
from utils import emit_and_print_errors


def run(name, expr):
    """
    Emit and print the errors we get for the below grammar with "expr" as
    a property in BarNode.
    """

    global FooNode, BarNode, MyStruct

    Diagnostics.set_lang_source_dir(path.abspath(__file__))

    print('== {} =='.format(name))

    class MyStruct(Struct):
        a = Field(type=LongType)
        b = Field(type=LongType)

    @root_grammar_class()
    class FooNode(ASTNode):
        pass

    class BarNode(FooNode):
        prop = Property(expr)

    def lang_def():
        foo_grammar = Grammar('main_rule')
        foo_grammar.add_rules(
            main_rule=Row('example') ^ BarNode,
        )
        return foo_grammar
    emit_and_print_errors(lang_def)
    print('')


run("Correct code", lambda: New(MyStruct, a=Literal(12), b=Literal(15)))
run("Incorrect new 1", lambda: New(MyStruct, a=Literal(12)))
run("Incorrect new 2", lambda: New(MyStruct, a=Literal(12), b=No(FooNode)))
run("Incorrect new 1", lambda: New(MyStruct, a=Literal(12), b=Literal(15),
                                   c=Literal(19)))
print 'Done'
