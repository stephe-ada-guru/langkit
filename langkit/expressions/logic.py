import funcy

from langkit.compiled_types import (
    LogicVarType, EquationType, BoolType, T
)

from langkit.diagnostics import check_multiple, check_source_language
from langkit.expressions.base import (
    AbstractExpression, BuiltinCallExpr, LiteralExpr, PropertyDef,
    ResolvedExpression, construct, BasicExpr, auto_attr
)
from langkit.expressions.envs import Env
from langkit.names import Name


def untyped_literal_expr(expr_str):
    """
    Create an untyped LiteralExpr instance for "expr_str" and return it.

    This is a helper for code that generates expressions which have no
    corresponding CompiledType in Langkit. Materializing such values in
    ResolvedExpression trees can be useful anayway to leverage BuiltinCallExpr
    code generation capabilities, in particular temporary creation for the
    result. We can do this because BuiltinCallExpr does not need its operands'
    types to be valid.

    :param str expr_str: The generated code for this literal expression.
    :rtype: LiteralExpr
    """
    return LiteralExpr(expr_str, None)


class Bind(AbstractExpression):
    """
    This expression binds two logic variables A and B, through a property call,
    so that, in logical terms::

        B = A.property_call()

    Which is expressed in the DSL as::

        Bind(A, B, property)
    """

    def __init__(self, from_expr, to_expr, conv_prop=None, eq_prop=None):
        """
        :param AbstractExpression from_expr: An expression resolving to a
            logical variable that is the source of the bind.
        :param AbstractExpression to_expr: An expression resolving to a
            logical variable that is the destination of the bind.
        :param PropertyDef|None conv_prop: The property to apply on the
            value of from_expr that will yield the value to give to to_expr.
            For convenience, it can be a property on any subclass of the root
            ast node class, and can return any subclass of the root ast node
            class.
        :param PropertyDef|None eq_prop: The property to use to test for
            equality between the value of the two expressions. For convenience,
            it can be a property on a subclass of the root ast node class,
            however:

            1. It needs to take exactly two parameters, the self parameter and
               another parameter.
            2. The two parameters must be of exactly the same type.
        """
        super(Bind, self).__init__()
        self.from_expr = from_expr
        self.to_expr = to_expr
        self.conv_prop = conv_prop
        self.eq_prop = eq_prop

    def do_prepare(self):
        from langkit.compile_context import get_context

        get_context().do_generate_logic_binder(self.conv_prop, self.eq_prop)

    def construct(self):
        # We have to wait for the construct pass for the following checks
        # because they rely on type information, which is not supposed to be
        # computed before this pass.
        if self.conv_prop:
            check_multiple([
                (self.conv_prop.type.matches(T.root_node),
                 "The property passed to bind must return a subtype "
                 "of {}".format(T.root_node.name().camel)),

                (self.conv_prop.struct.matches(T.root_node),
                 "The property passed to bind must belong to a subtype "
                 "of {}".format(T.root_node.name().camel))
            ])

        # Those checks are run in construct, because we need the eq_prop to be
        # prepared already, which is not certain in do_prepare (order
        # dependent).

        if self.eq_prop:
            args = self.eq_prop.explicit_arguments
            check_multiple([
                (self.eq_prop.type == BoolType,
                 "Equality property must return boolean"),

                (self.eq_prop.struct.matches(T.root_node),
                 "The equality property passed to bind must belong to a "
                 "subtype of {}".format(T.root_node.name().camel)),

                (len(args) == 1,
                 "Expected 1 argument for eq_prop, got {}".format(len(args))),

            ])
            check_source_language(
                args[0].type == self.eq_prop.struct,
                "Self and first argument should be of the same type"
            )

        cprop_uid = (self.conv_prop.uid if self.conv_prop else "Default")
        eprop_uid = (self.eq_prop.uid if self.eq_prop else "Default")
        pred_func = untyped_literal_expr(
            "Logic_Converter_{}'(Env => {})".format(
                cprop_uid, construct(Env).render_expr()
            )
            if self.conv_prop
            else "No_Logic_Converter_Default"
        )

        def construct_operand(op):
            from langkit.expressions import Cast, New
            expr = construct(op)

            check_source_language(

                expr.type == LogicVarType
                or expr.type.matches(T.root_node)
                or expr.type.matches(T.root_node.env_el()),

                "Operands to a logic bind operator should be either "
                "a logic variable or an ASTNode, got {}".format(expr.type)
            )

            if expr.type.matches(T.root_node.env_el()):
                if expr.type is not T.root_node.env_el():
                    expr = Cast.Expr(expr, T.root_node.env_el())
            elif expr.type.matches(T.root_node):
                # Cast the ast node type if necessary
                if expr.type is not T.root_node:
                    expr = Cast.Expr(expr, T.root_node)

                # If the expression is a root node, implicitly construct an
                # env_element from it.
                expr = New.StructExpr(T.root_node.env_el(), {
                    Name('El'): expr,
                    Name('MD'): LiteralExpr('<>', None),
                    Name('Parents_Bindings'): LiteralExpr('null', None)
                })

            return expr

        lhs = construct_operand(self.from_expr)
        rhs = construct_operand(self.to_expr)

        return BuiltinCallExpr(
            "Bind_{}_{}.Create".format(cprop_uid, eprop_uid),
            EquationType,
            [lhs, rhs, pred_func],
            "Bind_Result"
        )


class DomainExpr(ResolvedExpression):
    static_type = EquationType

    def __init__(self, domain, logic_var_expr):
        self.domain = domain
        ":type: ResolvedExpression"

        self.logic_var_expr = logic_var_expr
        ":type: ResolvedExpression"

        self.res_var = PropertyDef.get().vars.create("Var", EquationType)

        super(DomainExpr, self).__init__()

    def _render_pre(self):
        is_node_domain = (
            self.domain.static_type.element_type().is_env_element_type
        )

        return "\n".join([
            self.domain.render_pre(),
            self.logic_var_expr.render_pre(), """
            declare
                Dom : {domain_type} := {domain};
                A   : Eq_Node.Raw_Member_Array (1 .. Length (Dom));
            begin
                for J in 0 .. Length (Dom) - 1 loop
                    A (J + 1) := {env_el};
                end loop;

                {res_var} := Member ({logic_var}, A);
            end;
            """.format(logic_var=self.logic_var_expr.render_expr(),
                       domain=self.domain.render_expr(),
                       domain_type=self.domain.type.name(),
                       res_var=self.res_var.name,
                       env_el="Get (Dom, J)" if is_node_domain
                       else "(El => Get (Dom, J), others => <>)")
        ])

    def _render_expr(self):
        return str(self.res_var.name)

    @property
    def subexprs(self):
        return {'domain': self.domain, 'logic_var_expr': self.logic_var_expr}


@auto_attr
def domain(logic_var_expr, domain):
    """
    Define the domain of a logical variable. Several important properties about
    this expression:

    This is the entry point into the logic DSL. A variable of LogicVarType
    *must* have a domain defined in the context of an equation. If it doesn't,
    its solution set is empty, and thus the only possible value for it is
    undefined.

    If an equation is defined in which the only constraint on variables is
    their domains, then, for a set A, B, .., N of logical variables, with
    domains DA, DB, .., DN, the set of solutions will be of the product of the
    set of every domains.

    So for example, in the equation::
        Domain(A, [1, 2]) and Domain(B, [1, 2])

    The set of solutions is::
        [(1, 1), (1, 2), (2, 1), (2, 2)]

    The 'or' operator acts like concatenation on domains of logic variable, so
    for example::

        Domain(A, [1, 2]) or Domain(A, [3, 4])

    is equivalent to (but slower than) Domain(A, [1, 2, 3, 4]).

    You can define an equation that is invalid, in that not every equation has
    a domain, and, due to runtime dispatch , we cannot statically predict if
    that's gonna happen. Thus, trying to solve such an equation will result in
    an error.

    Please note that for the moment equations can exist only on AST nodes,
    so the above examples are invalid, and just meant to illustrate the
    semantics.

    :param AbstractExpression logic_var_expr: An expression
        that must resolve to an instance of a logic variable.
    :param AbstractExpression domain: An expression that must resolve to
        the domain, which needs to be a collection of a type that
        derives from the root grammar class, or the root grammar class
        itself.
    """
    return DomainExpr(
        construct(domain, lambda d: d.is_collection(), "Type given "
                  "to LogicVar must be collection type, got {expr_type}"),
        construct(logic_var_expr, LogicVarType)
    )


class Predicate(AbstractExpression):
    """
    The predicate expression will ensure that a certain property is maintained
    on one or several logical variables in all possible solutions, so that the
    only solutions in the equations are the equations where the property is
    True.

    Expressions that are passed that are not logical variables will be passed
    as extra arguments to the property, so their types need to match::

        class BaseNode(ASTNode):
            a = UserField(LogicVarType)
            b = UserField(LogicVarType)

            @langkit_property(return_type=BoolType)
            def test_property(other_node=BaseNode, int_arg=LongType):
                ...

            # This is a valid Predicate instantiation for the above property
            equation = Property(
                Predicate(FooNode.fields.test_property, Self.a, Self.b, 12)
            )

    """

    def __init__(self, pred_property, *exprs):
        """
        :param PropertyDef pred_property: The property to use as a predicate.
            For convenience, it can be a property of any subtype of the root
            ast node, but it needs to return a boolean.

        :param [AbstractExpression] exprs: Every argument to pass to the
            predicate, logical variables first, and extra arguments last.
        """
        super(Predicate, self).__init__()
        self.pred_property = pred_property
        self.exprs = exprs

    def construct(self):
        check_multiple([
            (isinstance(self.pred_property, PropertyDef),
             "Needs a property reference, got {}".format(self.pred_property)),

            (self.pred_property.type.matches(BoolType),
             "The property passed to predicate must return a boolean, "
             "got {}".format(self.pred_property.type.name().camel)),

            (self.pred_property.struct.matches(T.root_node),
             "The property passed to bind must belong to a subtype "
             "of {}".format(T.root_node.name().camel))
        ])

        exprs = [construct(e) for e in self.exprs]

        prop_types = [self.pred_property.struct] + [
            a.type for a in self.pred_property.explicit_arguments
        ]

        # Separate logic variable expressions from extra argument expressions
        logic_var_exprs, closure_exprs = funcy.split_by(
            lambda e: e.type == LogicVarType, exprs
        )

        check_source_language(
            len(logic_var_exprs) > 0, "Predicate instantiation should have at "
            "least one logic variable expression"
        )

        check_source_language(
            all(e.type != LogicVarType for e in closure_exprs), "Logic "
            "variable expressions should be grouped at the beginning, and "
            "should not appear after non logic variable expressions"
        )

        for i, (expr, arg_type) in enumerate(zip(exprs, prop_types)):
            if expr.type == LogicVarType:
                check_source_language(
                    arg_type.matches(T.root_node), "Argument #{} of predicate "
                    "is a logic variable, the corresponding property formal "
                    "has type {}, but should be a descendent of {}".format(
                        i, arg_type.name().camel, T.root_node.name().camel
                    )
                )
            else:
                check_source_language(
                    expr.type.matches(arg_type), "Argument #{} of predicate "
                    "has type {}, should be {}".format(
                        i, expr.type.name().camel, arg_type.name().camel
                    )
                )

        pred_id = self.pred_property.do_generate_logic_predicate(*[
            e.type for e in closure_exprs
        ])

        closure_exprs.append(construct(Env))

        # Append the debug image for the predicate
        closure_exprs.append(LiteralExpr('"{}.{}"'.format(
            self.pred_property.name.camel_with_underscores,
            self.pred_property.struct.name().camel_with_underscores
        ), type=None))

        logic_var_exprs.append(
            BasicExpr("{}_Predicate_Caller'({})".format(
                pred_id, ", ".join(
                    ["{}" for _ in range(len(closure_exprs) - 2)]
                    + ["Env => {}, "
                       "Dbg_Img => (if Debug then new String'({})"
                       "            else null)"]
                )
            ), type=None, operands=closure_exprs)
        )

        return BuiltinCallExpr(
            "{}_Pred.Create".format(pred_id), EquationType, logic_var_exprs,
            result_var_name="Pred"
        )


@auto_attr
def get_value(logic_var):
    """
    Expression that'll extract the value out of a logic variable. The type is
    always the root grammar class.

    :param AbstractExpression logic_var: The logic var from which we want to
        extract the value.
    """
    return BuiltinCallExpr(
        "Eq_Node.Refs.GetL", T.root_node.env_el(),
        [construct(logic_var, LogicVarType)]
    )


@auto_attr
def solve(equation):
    """
    Expression that will call solve on an instance of EquationType,
    and return whether any solution was found or not. The solutions are not
    returned, instead, logic variables are bound to their values in the
    current solution.

    TODO: For the moment, since properties returning equations will
    reconstruct them everytime, there is no way to get the second solution
    if there is one. Also you cannot do that manually either since a
    property exposing equations cannot be public at the moment.

    :param AbstractExpression equation: The equation to solve.
    """
    return BuiltinCallExpr("Solve", BoolType,
                           [construct(equation, EquationType)])


class LogicBooleanOp(AbstractExpression):
    """
    Internal Expression that will combine sub logic expressions via an Or or
    an And logic operator.
    """

    KIND_OR = 0
    KIND_AND = 1

    def __init__(self, equation_array, kind=KIND_OR):
        """
        :param AbstractExpression equation_array: An array of equations to
            logically combine via the or operator.
        """
        super(LogicBooleanOp, self).__init__()
        self.equation_array = equation_array
        self.kind = kind

    def construct(self):
        return BasicExpr(
            "Variadic_{} (Relation_Array ({{}}.Items))".format(
                "Or" if self.kind == self.KIND_OR else "And"
            ),
            EquationType,
            [construct(self.equation_array, EquationType.array_type())],
            result_var_name="Logic_Boolean_Op"
        )


class Any(LogicBooleanOp):
    """
    Expression that will combine sub logic expressions via an Or logic
    operator. Use this when you have an unbounded number of sub-equations to
    bind. The parameter is an array of equations.
    """

    def __init__(self, equation_array):
        super(Any, self).__init__(equation_array, LogicBooleanOp.KIND_OR)


class All(LogicBooleanOp):
    """
    Expression that will combine sub logic expressions via an And logic
    operator. Use this when you have an unbounded number of sub-equations to
    bind. The parameter is an array of equations.
    """

    def __init__(self, equation_array):
        super(All, self).__init__(equation_array, LogicBooleanOp.KIND_AND)


class LogicTrue(AbstractExpression):
    """
    An equation that always return True.
    """

    def __init__(self):
        super(LogicTrue, self).__init__()

    def construct(self):
        return LiteralExpr("True_Rel", type=EquationType,
                           result_var_name="Logic_True")


class LogicFalse(AbstractExpression):
    """
    An equation that always return False.
    """

    def __init__(self):
        super(LogicFalse, self).__init__()

    def construct(self):
        return LiteralExpr("False_Rel", type=EquationType,
                           result_var_name="Logic_False")
