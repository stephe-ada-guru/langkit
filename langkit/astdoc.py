import documentation


def write_astdoc(context, file):
    """
    Generate a synthetic text documentation about AST nodes and types.

    :param CompileContext context: Compile contxt from which types to document
        are retreived.
    :param file file: Output file for the documentation.
    """
    # Because of circular dependencies between compiled_types and
    # compile_context, we need to delay the following import.
    import compiled_types

    i = 0
    for type_decl in context.enum_declarations:
        typ = type_decl.type
        i += 1
        print >> file, 'enum {}:'.format(typ.name().camel)
        doc = typ.doc()
        if doc:
            print >> file, documentation.format_text(doc, 4)
        print >> file, '    {}'.format(
            ' '.join(typ.alternatives)
        )
        print >> file, ''

    if i > 0:
        print >> file, ''

    i = 0
    for typ in context.astnode_types:
        if i > 0:
            print >> file, ''
        i += 1

        # If this is not ASTNode, get the parent class
        bases = list(typ.get_inheritance_chain())
        base = bases[-2] if len(bases) > 1 else None
        abs_fields = list(typ.get_abstract_fields())

        print >> file, '{}node {}{}{}'.format(
            'abstract ' if typ.abstract else '',
            typ.name().camel,
            '({})'.format(base.name().camel) if base else '',
            ':' if abs_fields else ''
        )
        doc = typ.doc()
        if doc:
            print >> file, documentation.format_text(doc, 4)
            print >> file, ''

        for abs_field in abs_fields:
            inherit_note = (
                '' if abs_field.ast_node == typ else
                ' [inherited from {}]'.format(
                    abs_field.ast_node.name().camel
                )
            )
            print >> file, '    {} {}: {}{}'.format(
                ('field'
                 if isinstance(abs_field, compiled_types.Field) else
                 'property'),
                abs_field.name.lower,
                abs_field.type.name().camel,
                inherit_note
            )
            doc = abs_field.doc()
            if doc:
                print >> file, documentation.format_text(doc, 8)