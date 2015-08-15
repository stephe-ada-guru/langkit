## vim: filetype=makocpp

#ifndef ${capi.header_guard_id}
#define ${capi.header_guard_id}

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Initialize the library. Must be called before anything else from this
   library and from Langkit_Support.  */
void ${capi.lib_name}_initialize(void);

/* Context for all source analysis.  */
typedef void* ${analysis_context_type};

/* Context for the analysis of a single compilation unit.  References are
   ref-counted.  */
typedef void* ${analysis_unit_type};

/* Data type for all AST nodes.  AST nodes are assembled to make up a tree.
   See the AST node primitives below to inspect such trees.  References are
   ref-counted.  */
typedef void* ${node_type};

/* Kind of AST nodes in parse trees.  */
typedef enum {
    /* TODO: do we keep a single node kind for all lists or should we
       specialize them?  */
    ${capi.get_name(Name("List"))} = 1,
% for astnode in _self.astnode_types:
    % if not astnode.abstract:
        ${capi.get_name(astnode.name())}
          = ${ctx.node_kind_constants[astnode]},
    % endif
% endfor
} ${node_kind_type};

/* Data type for tokens.  Tokens always come from AST node and have the same
   lifetime than the AST node they come from.  */
typedef void* ${token_type};


/* Helper data structures for source location handling.  */

typedef struct {
    uint32_t line;
    uint16_t column;
} ${sloc_type};

typedef struct {
    ${sloc_type} start;
    ${sloc_type} end;
} ${sloc_range_type};


/* Analysis unit diagnostics.  */
typedef struct {
    ${sloc_range_type} sloc_range;
    /* Copy of the diagnostic message: once a diagnostic is retrieved through
       the API, the corresponding message must be free'd.  */
    char *message;
} ${diagnostic_type};


/*
 * Data structures held in AST nodes
 */


% for chunk in _self.c_astnode_field_types.values():
    ${chunk}
% endfor

/* Get the text of the given token.  The returned string is a copy and thus
   must be free'd by the caller.  */
char *${capi.get_name("token_text")} (${token_type} token);


/*
 * Analysis primitives
 */

/* Create and return an analysis context.  The caller is responsible to destroy
   it when done with it.  */
extern ${analysis_context_type}
${capi.get_name("create_analysis_context")}(void);

/* Destroy an analysis context.  Any analysis units it contains may survive if
   there are still references to it.  */
extern void
${capi.get_name("destroy_analysis_context")}(
        ${analysis_context_type} context);

/* Create a new analysis unit for Filename or return the existing one if
   any. If Reparse is true and the analysis unit already exists, reparse it
   from Filename.

   The result is owned by the context: the caller must increase its ref.
   count in order to keep a reference to it.

   On file opening failure, return a null address and in this case, if the
   analysis unit did not exist yet, do not register it.  */
extern ${analysis_unit_type}
${capi.get_name("get_analysis_unit_from_file")}(
        ${analysis_context_type} context,
        const char *filename,
        int reparse);

/* Create a new analysis unit for Filename or return the existing one if
   any. Whether the analysis unit already exists or not, (re)parse it from
   the source code in Buffer.

   The result is owned by the context: the caller must increase its ref.
   count in order to keep a reference to it.

   On file opening failure, return a null address and in this case, if the
   analysis unit did not exist yet, do not register it.  In this case, if
   the analysis unit was already existing, this preserves the AST.  */
extern ${analysis_unit_type}
${capi.get_name("get_analysis_unit_from_buffer")}(
        ${analysis_context_type} context,
        const char *filename,
        const char *buffer,
        size_t buffer_size);

/* Remove the corresponding analysis unit from this context.  Note that if
   someone still owns a reference to this unit, it is still available.  Return
   whether the removal was successful (i.e. whether the analysis unit
   existed). */
extern int
${capi.get_name("remove_analysis_unit")}(${analysis_context_type} context,
                                         const char *filename);

/* Return the root AST node for this unit, or NULL if there is none.  */
extern ${node_type}
${capi.get_name("unit_root")}(${analysis_unit_type} unit);

/* Return the number of diagnostics associated to this unit.  */
extern unsigned
${capi.get_name("unit_diagnostic_count")}(${analysis_unit_type} unit);

/* Get the Nth diagnostic in this unit and store it into *DIAGNOSTIC_P.  Return
   zero on failure (when N is too big).  */
extern int
${capi.get_name("unit_diagnostic")}(${analysis_unit_type} unit,
                                    unsigned n,
                                    ${diagnostic_type} *diagnostic_p);

/* Increase the reference count to an analysis unit.  Return the reference for
   convenience.  */
extern ${analysis_unit_type}
${capi.get_name("unit_incref")}(${analysis_unit_type} unit);

/* Decrease the reference count to an analysis unit.  */
extern void
${capi.get_name("unit_decref")}(${analysis_unit_type} unit);

/* Reparse an analysis unit from the associated file.

   Return whether reparsing was successful (i.e. whether we could read the
   source file).  If there was an error, preserve the existing AST and
   diagnostics.  */
extern int
${capi.get_name("unit_reparse_from_file")}(${analysis_unit_type} unit);

/* Reparse an analysis unit from a buffer.  */
extern void
${capi.get_name("unit_reparse_from_buffer")} (${analysis_unit_type} unit,
                                              const char *buffer,
                                              size_t buffer_size);

/* Free "str".  This is a convenience function for bindings.  */
extern void
${capi.get_name("free_str")}(char *str);


/*
 * General AST node primitives
 */

/* Get the kind of an AST node.  */
extern ${node_kind_type}
${capi.get_name("node_kind")}(${node_type} node);

/* Helper for textual dump: return the name of a node kind.  The returned
   string is a copy and thus must be free'd by the caller.  */
extern char*
${capi.get_name("kind_name")}(${node_kind_type} kind);

/* Get the spanning source location range for an AST node.  */
extern void
${capi.get_name("node_sloc_range")}(${node_type} node,
                                    ${sloc_range_type} *sloc_range);

/* Return the bottom-most AST node from NODE that contains SLOC, or NULL if
   there is none.  */
extern ${node_type}
${capi.get_name("lookup_in_node")}(${node_type} node,
                                   const ${sloc_type} *sloc);

/* Return the lexical parent of NODE, if any.  Return NULL for the root AST
   node or for AST nodes for which no one has a reference to the parent.  */
extern ${node_type}
${capi.get_name("node_parent")}(${node_type} node);

/* Return the number of AST node in NODE's fields.  */
extern unsigned
${capi.get_name("node_child_count")}(${node_type} node);

/* Get the Nth child AST node in NODE's fields and store it into *CHILD_P.
   Return zero on failure (when N is too big).  */
extern int
${capi.get_name("node_child")}(${node_type} node,
                               unsigned n,
                               ${node_type}* child_p);

/* Increase the reference count to an AST node.  Return the reference for
   convenience.  */
extern ${node_type}
${capi.get_name("node_incref")}(${node_type} node);

/* Decrease the reference count to an AST node.  */
extern void
${capi.get_name("node_decref")}(${node_type} node);


/*
 * Kind-specific AST node primitives
 */

/* All these primitives return their result through an OUT parameter.  They
   return a boolean telling whether the operation was successful (it can fail
   if the node does not have the proper type, for instance).  When an AST node
   is returned, its ref-count is left as-is.  */

% for astnode in _self.astnode_types:
    % for primitive in _self.c_astnode_primitives[astnode]:
        ${primitive.c_declaration}
    % endfor
% endfor


/*
 * Extensions handling
 */

/* The following functions make it possible to attach arbitrary data to AST
   nodes: these are extensions.  Each data is associated with both an extension
   ID and a destructor.  AST nodes can have either none or only one extension
   for a given ID.  The destructor is called when the AST node is about to be
   destroyed itself.

   This mechanism is inteded to ease annotating trees with analysis data but
   also to host node wrappers for language bindings.  */

/* Type for extension destructors.  The parameter are the "node" the extension
   was attached to and the "extension" itself.  */
typedef void (*${capi.get_name("node_extension_destructor")})(${node_type} node,
                                                              void *extension);

/* Register an extension and return its identifier.  Multiple calls with the
   same name will return the same identifier.  */
extern unsigned
${capi.get_name("register_extension")}(const char *name);

/* Create an extension slot in "node".  If this node already contains an
   extension for "ext_id", return the existing slot.  If not, create such a
   slot, associate the "dtor" destructor to it and initialize the slot to NULL.
   Return a pointer to the slot.

   Note that the pointer is not guaranteed to stay valid after further calls to
   this function.  */
extern void **
${capi.get_name("node_extension")}(${node_type} node,
                                   unsigned ext_id,
                                   ${capi.get_name("node_extension_destructor")} dtor);

#ifdef __cplusplus
}
#endif

#endif