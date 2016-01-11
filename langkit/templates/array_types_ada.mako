## vim: filetype=makoada

<%def name="public_decl(cls)">

   <% elt_type = cls.element_type() %>

   type ${cls.api_name()} is array (Positive range <>) of ${elt_type.name()};
   type ${cls.pointed()} (N : Natural) is record
      Items : ${cls.api_name()} (1 .. N);
   end record;

   type ${cls.name()} is access all ${cls.pointed()};

   ## If we are on the root grammar class type, we need a conversion function
   ## to be able to get element arrays starting from 0 and convert them into
   ## arrays starting from 1. We need it to convert from env element arrays,
   ## that are arrays of instances of the root grammar class, to our array
   ## record type.
   % if cls.element_type() == ctx.root_grammar_class:
   function Copy is new AST_Envs.Element_Arrays.Copy
     (Positive, ${cls.api_name()});

   function Create (Items : AST_Envs.Element_Array) return ${cls.name()}
   is (new ${cls.pointed()}'(Items => Copy (Items), N => Items'Length));
   % endif

   package ${cls.pkg_vector()} is new Langkit_Support.Vectors
     (${elt_type.name()});

</%def>