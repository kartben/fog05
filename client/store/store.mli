open Core

type t

(* type store_value *)

val create : string -> string -> string -> t

val put : t -> string -> string -> t

val dput : t -> string -> string option -> t

val get : t -> string -> string * string

val get_all : t -> string -> (string * string) list

val resolve_all : t -> string -> (string * string) list

val remove : t -> string -> t
