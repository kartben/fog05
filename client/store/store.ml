open Core
open Printf
open Lwt.Infix
open Websocket
open Websocket_lwt




type t = {
  sid : string;
  root : string;
  home : string;
}


(* type store_value = {
  key : string;
  value : string;
} *)

let store_server = "127.0.0.1"
let store_auth = "a1b2c3d4"
let store_port = 9876
(* 9876 for the CLI  *)

let interact addr uri command =
  (* print_endline ">>> interacting...." ; *)
  let resp = ref "" in
  let open Conduit_lwt_unix in
  let open Frame in
  let ctx = default_ctx in
  with_connection ~ctx:ctx addr uri >>= fun (recv, send) ->
  (* print_endline ">>> wsock created...." ; *)
  let react fr =
    (* print_endline ">>> reacting...." ; *)
    match fr.opcode with
    | Opcode.Ping ->
      send @@ Frame.create ~opcode:Opcode.Pong ()
    | Opcode.Close ->
      send @@ Frame.create ~opcode:Opcode.Close () >>= fun () -> Lwt.fail Exit

    | Opcode.Binary ->
      (* print_endline ">> Received binary data: " ;
      print_endline fr.content; *)
      Lwt.return_unit

    | Opcode.Text ->
      (* print_endline ">> Received text data: " ; *)
      (* print_endline fr.content; *)
      resp := fr.content;
      (* Lwt.return fr.content *)
      Lwt.return_unit
    | _ ->
      send @@ Frame.close 1002 >>= fun () -> Lwt.fail Exit
  in
  let pullf () =
  Lwt.wrap ( fun () -> (
        (* print_endline ">> Check result" ; *)
        while !resp = "" do ignore !resp done; !resp)
    )
  in
  let rec react_forever () =
    (* print_endline ">>> react_forever...." ; *)
    recv () >>= react >>= pullf
  in
  let pushf () =
    (* print_endline ">> Sending command" ; *)
    send @@ Frame.create ~content:command ()

  in pushf () >>= react_forever


(* mvar *)

let create store_id  store_root  store_home =
  let cmd = sprintf "create %s %s %s 1024" store_id store_root store_home in
  let url = sprintf "ws://%s:%d/%s" store_server store_port store_auth in
  let addr = `TCP ( `IP (Ipaddr.of_string_exn store_server), `Port (store_port)) in
  let ws_uri = Uri.of_string url in
  let result = Lwt_main.run @@ interact addr ws_uri cmd in
  if String.is_prefix result ~prefix:"OK" then
    {sid = store_id ; root = store_root; home = store_home;}
  else
    failwith "store error"


let put store uri value =
  let cmd = sprintf "put %s %s %s" store.sid uri value in
  let url = sprintf "ws://%s:%d/%s" store_server store_port store_auth in
  let addr = `TCP ( `IP (Ipaddr.of_string_exn store_server), `Port (store_port)) in
  let ws_uri = Uri.of_string url in
  let result = Lwt_main.run @@ interact addr ws_uri cmd in
  if String.is_prefix result ~prefix:"OK" then
    store
  else
    failwith "store error"

let dput store uri value =
  let cmd = match value with
    | None -> sprintf "dput %s %s" store.sid uri
    | Some s -> sprintf "dput %s %s %s" store.sid uri s
  in
  let url = sprintf "ws://%s:%d/%s" store_server store_port store_auth in
  let addr = `TCP ( `IP (Ipaddr.of_string_exn store_server), `Port (store_port)) in
  let ws_uri = Uri.of_string url in
  let result = Lwt_main.run @@ interact addr ws_uri cmd in
  if String.is_prefix result ~prefix:"OK" then
    store
  else
    failwith "store error"

let get store uri =
  let cmd = sprintf "get %s %s" store.sid uri in
  let url = sprintf "ws://%s:%d/%s" store_server store_port store_auth in
  let addr = `TCP ( `IP (Ipaddr.of_string_exn store_server), `Port (store_port)) in
  let ws_uri = Uri.of_string url in
  let result = Lwt_main.run @@ interact addr ws_uri cmd in
  if String.is_prefix result ~prefix:" value" then (
    let sv = String.split result ~on:' ' in
    let _,last_n = List.split_n sv 4 in
      (List.nth_exn sv 3, String.concat @@ last_n )
    )
  else
    failwith "error on store"


let remove store uri =
      let cmd = sprintf "remove %s %s" store.sid uri in
      let url = sprintf "ws://%s:%d/%s" store_server store_port store_auth in
      let addr = `TCP ( `IP (Ipaddr.of_string_exn store_server), `Port (store_port)) in
      let ws_uri = Uri.of_string url in
      let result = Lwt_main.run @@ interact addr ws_uri cmd in
      if String.is_prefix result ~prefix:"OK" then
        store
      else
        failwith "store error"

let get_all store uri =
  let cmd = sprintf "aget %s %s" store.sid uri in
  let url = sprintf "ws://%s:%d/%s" store_server store_port store_auth in
  let addr = `TCP ( `IP (Ipaddr.of_string_exn store_server), `Port (store_port)) in
  let ws_uri = Uri.of_string url in
  let result = Lwt_main.run @@ interact addr ws_uri cmd in
  if String.is_prefix result ~prefix:" values" then (
    let sv = List.nth_exn (String.split result ~on:' ') 4 in
    let values = String.split sv ~on:'|' in
    let res = List.map values ~f:(fun e -> let xs = String.split e ~on:'@' in (List.nth_exn xs 0,String.concat @@  List.tl_exn xs))
    in res
    )
  else
    failwith "error on store"


let resolve_all store uri =
  let cmd = sprintf "aresolve %s %s" store.sid uri in
  let url = sprintf "ws://%s:%d/%s" store_server store_port store_auth in
  let addr = `TCP ( `IP (Ipaddr.of_string_exn store_server), `Port (store_port)) in
  let ws_uri = Uri.of_string url in
  let result = Lwt_main.run @@ interact addr ws_uri cmd in
  if String.is_prefix result ~prefix:" values" then (
    let sv = String.chop_prefix_exn result (sprintf " values %s %s " store.sid uri ) in
    let values = String.split sv ~on:'|' in
    let res = List.map values ~f:(fun e -> let xs = String.split e ~on:'@' in (List.nth_exn xs 0,String.concat @@ List.tl_exn xs))
    in res
    )
  else
    failwith "error on store"
