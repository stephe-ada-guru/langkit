generic
   type T is private;
   Memo_Size : Positive := 16;
package Langkit_Support.Packrat is

   type Memo_State is (No_Result, Failure, Success);

   type Memo_Entry is record
      State             : Memo_State;
      Instance          : T;
      Offset, Final_Pos : Integer;
   end record;

   type Memo_Type is private;

   procedure Clear (Memo : in out Memo_Type);
   function Get (Memo : Memo_Type; Offset : Integer) return Memo_Entry
     with Inline_Always;

   procedure Set (Memo              : in out Memo_Type;
                  Is_Success        : Boolean;
                  Instance          : T;
                  Offset, Final_Pos : Integer)
     with Inline_Always;

private

   type Memo_Type is array (0 .. Memo_Size - 1) of Memo_Entry;

end Langkit_Support.Packrat;