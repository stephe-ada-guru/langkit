from langkit.compiled_types import (
    ASTNode, root_grammar_class, LongType
)
from langkit.diagnostics import Diagnostics
from langkit.expressions import Property, No
from langkit.parsers import Grammar, Row

from os import path
from utils import emit_and_print_errors


def run(name, expr):
    """
    Emit and print the errors we get for the below grammar with "expr" as
    a property in BarNode.
    """

    global FooNode

    Diagnostics.set_lang_source_dir(path.abspath(__file__))

    print('== {} =='.format(name))

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


run("Correct code", lambda: No(FooNode))
run("Incorrect No usage", lambda: No(LongType))
print 'Done'
