## vim: filetype=makoada

<% result = expr.result_var.name %>

${result} := new ${expr.static_type.value_type_name()};
Register_Destroyable (Self.Unit, ${root_node_type_name} (${result}));

## We consider the creator of a synthetized nodes as its parent even though
## the latter is not a regular child.
${result}.Parent := ${root_node_type_name} (Self);
${result}.Unit := Self.Unit;

## Keep the token start/end null, as expected for a synthetized node

% for name, fld_expr in expr._iter_ordered():
   ${result}.${name} := ${fld_expr.render_expr()};
% endfor
