## vim: filetype=makoada

with System;

with Langkit_Support.Token_Data_Handler;
use Langkit_Support.Token_Data_Handler;

--  Internal package used to provide interfaces types that help breaking
--  circular dependencies between Analysis_Unit and the root AST node
--  type definitions.

package ${_self.ada_api_settings.lib_name}.Analysis_Interfaces is

   type Analysis_Unit_Interface_Type is interface;
   type Analysis_Unit_Interface is
      access all Analysis_Unit_Interface_Type'Class;
   --  Internal interface type for Analysis_Unit, to be stored in AST nodes
   --  without trigerring circular dependencies.
   --
   --  TODO??? This is a kludge to be removed when we have time to investigate
   --  how to find a cleaner way to avoid circular elaboration.

   function Token_Data
     (Unit : access Analysis_Unit_Interface_Type)
      return Token_Data_Handler_Access is abstract;
   --  Get an access to the token data handler bundled in Unit. Note that this
   --  token data handler is not valid anymore as soon as Unit is destroyed or
   --  reparsed.

   type Destroy_Procedure is access procedure (Object : System.Address);

   procedure Register_Destroyable_Helper
     (Unit    : access Analysis_Unit_Interface_Type;
      Object  : System.Address;
      Destroy : Destroy_Procedure)
      is abstract;
   --  Internal implementation helper for Register_Destroyable. This is
   --  basically an untyped version of it, using System.Address instead of
   --  access types. This is required to we can store these values in the same
   --  place.

   generic
      type T is private;
      type T_Access is access all T;
      with procedure Destroy (Object : in out T_Access);
   procedure Register_Destroyable
     (Unit   : access Analysis_Unit_Interface_Type'Class;
      Object : T_Access);
   --  Generic procedure to register an object so that it is automatically
   --  destroyed when Unit is destroyed.

end ${_self.ada_api_settings.lib_name}.Analysis_Interfaces;