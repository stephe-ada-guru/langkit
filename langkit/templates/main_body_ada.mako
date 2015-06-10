## vim: filetype=makoada

with Ada.Text_IO; use Ada.Text_IO;
with Ada.Unchecked_Deallocation;

with ${_self.ada_api_settings.lib_name}.Parsers;
use ${_self.ada_api_settings.lib_name}.Parsers;

package body ${_self.ada_api_settings.lib_name} is

   procedure Destroy (Unit : Analysis_Unit);

   procedure Free is new Ada.Unchecked_Deallocation
     (Analysis_Context_Type, Analysis_Context);

   procedure Free is new Ada.Unchecked_Deallocation
     (Analysis_Unit_Type, Analysis_Unit);

   procedure Do_Parsing
     (Unit       : Analysis_Unit;
      Get_Parser : access function (TDH : Token_Data_Handler_Access)
                                    return Parser_Type);
   --  Helper for Get_Unit and the public Reparse procedures: parse an analysis
   --  unit using Get_Parser and replace Unit's AST_Root and the diagnostics
   --  with the parsers's output.

   function Get_Unit
     (Context    : Analysis_Context;
      Filename   : String;
      Reparse    : Boolean;
      Get_Parser : access function (TDH : Token_Data_Handler_Access)
                                    return Parser_Type)
      return Analysis_Unit;
   --  Helper for Get_From_File and Get_From_Buffer: do all the common work
   --  using Get_Parser to either parse from a file or from a buffer. Return
   --  the resulting analysis unit.
   --
   --  Get_Parser is allowed to raise a Name_Error exception if there reading a
   --  file does not work: resources will be correctly released in this case.

   ------------
   -- Create --
   ------------

   function Create return Analysis_Context is
   begin
      return new Analysis_Context_Type'
        (Units_Map => <>,
         Symbols   => Allocate);
   end Create;

   --------------
   -- Get_Unit --
   --------------

   function Get_Unit
     (Context    : Analysis_Context;
      Filename   : String;
      Reparse    : Boolean;
      Get_Parser : access function (TDH : Token_Data_Handler_Access)
                                    return Parser_Type)
      return Analysis_Unit
   is
      use Units_Maps;

      Fname   : constant Unbounded_String := To_Unbounded_String (Filename);
      Cur     : constant Cursor := Context.Units_Map.Find (Fname);
      Created : constant Boolean := Cur = No_Element;
      Unit    : Analysis_Unit;

   begin
      --  Create the Analysis_Unit if needed

      if Created then
         Unit := new Analysis_Unit_Type'
           (Context     => Context,
            Ref_Count   => 1,
            AST_Root    => null,
            File_Name   => Fname,
            TDH         => <>,
            Diagnostics => <>);
         Initialize (Unit.TDH, Context.Symbols);
      else
         Unit := Element (Cur);
      end if;

      --  (Re)parse it if needed

      if Created or else Reparse then
         begin
            begin
               Do_Parsing (Unit, Get_Parser);
            exception
               when Name_Error =>
                  if Created then
                     Dec_Ref (Unit);
                  end if;
                  raise;
            end;
         end;
      end if;

      if Created then
         Context.Units_Map.Insert (Fname, Unit);
      end if;

      return Unit;
   end Get_Unit;

   ----------------
   -- Do_Parsing --
   ----------------

   procedure Do_Parsing
     (Unit       : Analysis_Unit;
      Get_Parser : access function (TDH : Token_Data_Handler_Access)
                                    return Parser_Type)
   is
      Parser : Parser_Type := Get_Parser (Unit.TDH'Access);
   begin
      Dec_Ref (Unit.AST_Root);
      Unit.AST_Root := Parse (Parser);
      Unit.Diagnostics := Parser.Diagnostics;
      Clean_All_Memos;
   end Do_Parsing;

   -------------------
   -- Get_From_File --
   -------------------

   function Get_From_File (Context  : Analysis_Context;
                           Filename : String;
                           Reparse  : Boolean := False) return Analysis_Unit
   is
      function Get_Parser (TDH : Token_Data_Handler_Access) return Parser_Type
      is (Create_From_File (Filename, TDH));
   begin
      return Get_Unit (Context, Filename, Reparse, Get_Parser'Access);
   end Get_From_File;

   ---------------------
   -- Get_From_Buffer --
   ---------------------

   function Get_From_Buffer (Context  : Analysis_Context;
                             Filename : String;
                             Buffer   : String) return Analysis_Unit
   is
      function Get_Parser (TDH : Token_Data_Handler_Access) return Parser_Type
      is (Create_From_Buffer (Buffer, TDH));
   begin
      return Get_Unit (Context, Filename, True, Get_Parser'Access);
   end Get_From_Buffer;

   ------------
   -- Remove --
   ------------

   procedure Remove (Context   : Analysis_Context;
                     File_Name : String)
   is
      use Units_Maps;

      Cur : Cursor := Context.Units_Map.Find (To_Unbounded_String (File_Name));
   begin
      if Cur = No_Element then
         raise Constraint_Error with "No such analysis unit";
      end if;

      --  We remove the corresponding analysis unit from this context but
      --  users could keep references on it, so make sure it can live
      --  independently.

      declare
         Unit : constant Analysis_Unit := Element (Cur);
      begin
         Unit.Context := null;
         Dec_Ref (Unit);
      end;

      Context.Units_Map.Delete (Cur);
   end Remove;

   -------------
   -- Destroy --
   -------------

   procedure Destroy (Context : in out Analysis_Context) is
   begin
      for Unit of Context.Units_Map loop
         Unit.Context := null;
         Dec_Ref (Unit);
      end loop;
      Free (Context.Symbols);
      Free (Context);
   end Destroy;

   -------------
   -- Inc_Ref --
   -------------

   procedure Inc_Ref (Unit : Analysis_Unit) is
   begin
      Unit.Ref_Count := Unit.Ref_Count + 1;
   end Inc_Ref;

   -------------
   -- Dec_Ref --
   -------------

   procedure Dec_Ref (Unit : Analysis_Unit) is
   begin
      Unit.Ref_Count := Unit.Ref_Count - 1;
      if Unit.Ref_Count = 0 then
         Destroy (Unit);
      end if;
   end Dec_Ref;

   -------------
   -- Reparse --
   -------------

   procedure Reparse (Unit : Analysis_Unit) is
      function Get_Parser (TDH : Token_Data_Handler_Access) return Parser_Type
      is (Create_From_File (To_String (Unit.File_Name), TDH));
   begin
      Do_parsing (Unit, Get_Parser'Access);
   end Reparse;

   -------------
   -- Reparse --
   -------------

   procedure Reparse (Unit : Analysis_Unit; Buffer : String) is
      function Get_Parser (TDH : Token_Data_Handler_Access) return Parser_Type
      is (Create_From_Buffer (Buffer, TDH));
   begin
      Do_parsing (Unit, Get_Parser'Access);
   end Reparse;

   -------------
   -- Destroy --
   -------------

   procedure Destroy (Unit : Analysis_Unit) is
      Unit_Var : Analysis_Unit := Unit;
   begin
      Dec_Ref (Unit.AST_Root);
      Free (Unit.TDH);
      Free (Unit_Var);
   end Destroy;

   -----------
   -- Print --
   -----------

   procedure Print (Unit : Analysis_Unit) is
   begin
      if Unit.AST_Root = null then
         Put_Line ("<empty analysis unit>");
      else
         Unit.AST_Root.Print;
      end if;
   end Print;

   % for chunk in _self.primitives_bodies:
   ${chunk}
   % endfor

end ${_self.ada_api_settings.lib_name};