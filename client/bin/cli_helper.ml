open Core
open Types_t


let sid = "0"

let home = "localhost"
let aroot = sprintf "afos://%s" sid
let droot = sprintf "dfos://%s" sid
let ahome  = sprintf "%s/%s" aroot home
let dhome  = sprintf "%s/%s" droot home
let store_server = "localhost"
let store_auth = "a1b2cd4"

(* HELPER FUNCTIONS *)
let read_file filename =
  let res = In_channel.read_all filename in
  res

let check_manifest manifest parser validator =
  let res =
    try
      let n = parser manifest in
      validator [] n;
      Ok true
    with
    | e -> Error e
  in res

let load_manifest manifest parser =
  parser manifest

let get_all_nodes () =
  let s = Store.create (sprintf "a%s" home) aroot ahome in
  let res = Store.resolve_all s (sprintf "%s/*" aroot) in
  List.filter res ~f:(fun e -> let (k , v) = e in if (List.length @@ String.split k ~on:'/' = 4) then true else false)

let get_all_nodes_uuid () =
  let nodes = get_all_nodes () in
  List.map nodes ~f:(fun e -> let (k , v) = e in (Types_j.node_info_of_string v).uuid)

let get_all_node_plugin node_uuid =
  let s = Store.create (sprintf "a%s" home) aroot ahome in
  let (k,v) = Store.get s (sprintf "%s/%s/plugins" aroot node_uuid) in
  (Types_j.plugins_info_type_of_string v).plugins


let get_plugins_by_type (all_plugins : Types_j.plugin list) (plugin_type : string) =
  let plugins = List.filter all_plugins ~f:(fun e -> e.plugin_type = plugin_type) in
  plugins

let get_plugins_by_name (all_plugins : Types_j.plugin list) (pl_name : string) =
  let plugins = List.filter all_plugins ~f:(fun e -> String.is_substring ~substring:(String.uppercase pl_name) (String.uppercase e.name)) in
  plugins


let send_add_network_node (manifest : Types_j.network) node_uuid =
  let network = { manifest with status = Some "add"} in
  let s = Store.create (sprintf "d%s" home) droot dhome in
  let plugin = List.hd_exn (get_plugins_by_type (get_all_node_plugin node_uuid) "network") in
  let v =  Types_j.string_of_network network in
  Store.put s (sprintf "%s/%s/network/%s/networks/%s" droot node_uuid plugin.uuid network.uuid) v


let send_remove_network_node net_uuid node_uuid =
  let s = Store.create (sprintf "d%s" home) droot dhome in
  let plugin = List.hd_exn (get_plugins_by_type (get_all_node_plugin node_uuid) "network") in
  Store.remove s (sprintf "%s/%s/network/%s/networks/%s" droot node_uuid plugin.uuid net_uuid)


let get_flavors node_uuid =
  let uri = match node_uuid with
    | None -> sprintf "%s/*/runtime/*/flavor/*/" aroot
    | Some s -> sprintf "%s/%s/runtime/*/flavor/*/" aroot s
  in
  let s = Store.create (sprintf "a%s" home) aroot ahome in
  let res =  Store.resolve_all s uri in
  List.map res ~f:(fun e -> let (k , v) = e in Types_j.flavor_of_string v)


let send_add_flavor_node (manifest : Types_j.flavor) node_uuid =
  let flavor = { manifest with status = Some "add"} in
  let s = Store.create (sprintf "d%s" home) droot dhome in
  let plugins = List.append (get_plugins_by_name (get_plugins_by_type (get_all_node_plugin node_uuid) "runtime ") "KVMLibvirt") (get_plugins_by_name (get_plugins_by_type (get_all_node_plugin node_uuid) "runtime ") "XENLibvirt") in
  let v =  Types_j.string_of_flavor flavor in
  for i = 0 to (List.length plugins) -1 do
    ignore @@ Store.put s (sprintf "%s/%s/runtime/%s/flavor/%s" droot node_uuid (List.nth_exn plugins i).uuid flavor.uuid) v
  done

let send_remove_flavor_node flavor_uuid node_uuid =
  let s = Store.create (sprintf "d%s" home) droot dhome in
  let plugins = List.append (get_plugins_by_name (get_plugins_by_type (get_all_node_plugin node_uuid) "runtime ") "KVMLibvirt") (get_plugins_by_name (get_plugins_by_type (get_all_node_plugin node_uuid) "runtime ") "XENLibvirt") in
  for i = 0 to (List.length plugins) -1 do
    ignore @@ Store.remove s (sprintf "%s/%s/runtime/%s/flavor/%s" droot node_uuid (List.nth_exn plugins i).uuid flavor_uuid)
  done

let get_images node_uuid =
  let uri = match node_uuid with
    | None -> sprintf "%s/*/runtime/*/image/*/" aroot
    | Some s -> sprintf "%s/%s/runtime/*/image/*/" aroot s
  in
  let s = Store.create (sprintf "a%s" home) aroot ahome in
  let res =  Store.resolve_all s uri in
  List.map res ~f:(fun e -> let (_ , v) = e in Types_j.image_of_string v)

let send_add_image_node (manifest : Types_j.image) node_uuid =
  let image = { manifest with status = Some "add"} in
  let s = Store.create (sprintf "d%s" home) droot dhome in
  let plugins = List.append (get_plugins_by_name (get_plugins_by_type (get_all_node_plugin node_uuid) "runtime ") "KVMLibvirt") (get_plugins_by_name (get_plugins_by_type (get_all_node_plugin node_uuid) "runtime ") "XENLibvirt") in
  let v =  Types_j.string_of_image image in
  for i = 0 to (List.length plugins) -1 do
    ignore @@ Store.put s (sprintf "%s/%s/runtime/%s/image/%s" droot node_uuid (List.nth_exn plugins i).uuid image.uuid) v
  done

let send_remove_image_node image_uuid node_uuid =
  let s = Store.create (sprintf "d%s" home) droot dhome in
  let plugins = List.append (get_plugins_by_name (get_plugins_by_type (get_all_node_plugin node_uuid) "runtime ") "KVMLibvirt") (get_plugins_by_name (get_plugins_by_type (get_all_node_plugin node_uuid) "runtime ") "XENLibvirt") in
  for i = 0 to (List.length plugins) -1 do
    ignore @@ Store.remove s (sprintf "%s/%s/runtime/%s/image/%s" droot node_uuid (List.nth_exn plugins i).uuid image_uuid)
  done

let get_entity_handler_by_uuid node_uuid entity_uuid =
  let uri = sprintf "%s/%s/runtime/*/entity/%s" aroot node_uuid entity_uuid in
  let s = Store.create (sprintf "a%s" home) aroot ahome in
  let res = Store.resolve_all s uri in
  List.hd_exn (List.map res ~f:(fun e -> let (k,_) = e in List.nth_exn (String.split k ~on:'/') 5))

let get_entity_handler_by_type node_uuid t =
  List.hd_exn (get_plugins_by_name (get_all_node_plugin node_uuid) t)


let rec wait_atomic_entity_state_change node_uuid handler_uuid atomic_uuid state =
  let uri = sprintf "%s/%s/runtime/%s/entity/%s" aroot node_uuid handler_uuid atomic_uuid in
  let s = Store.create (sprintf "a%s" home) droot dhome in
  let (_,v) = Store.get s uri in
  Unix.sleep 1;
  if v = "" then wait_atomic_entity_state_change node_uuid handler_uuid atomic_uuid state
  else
    match (Types_j.atomic_entity_of_string v).status with
    | Some s -> if s = state then Ok true else wait_atomic_entity_state_change node_uuid handler_uuid atomic_uuid state
    | _ -> wait_atomic_entity_state_change node_uuid handler_uuid atomic_uuid state

let rec wait_atomic_entity_instance_state_change node_uuid handler_uuid atomic_uuid instance_uuid state =
  let uri = sprintf "%s/%s/runtime/%s/entity/%s/instance/%s" aroot node_uuid handler_uuid atomic_uuid instance_uuid in
  let s = Store.create (sprintf "a%s" home) droot dhome in
  let (_,v) = Store.get s uri in
  Unix.sleep 1;
  if v = "" then wait_atomic_entity_instance_state_change node_uuid handler_uuid atomic_uuid instance_uuid state
  else
    match (Types_j.atomic_entity_of_string v).status with
    | Some s -> if s = state then Ok true else wait_atomic_entity_instance_state_change node_uuid handler_uuid atomic_uuid instance_uuid state
    | _ -> wait_atomic_entity_instance_state_change node_uuid handler_uuid atomic_uuid instance_uuid state



let send_atomic_entity_define (manifest :Types_j.atomic_entity) node_uuid =
  let manifest = {manifest with status = Some "define"} in
  let handler = get_entity_handler_by_type node_uuid manifest.atomic_type in
  let uri = sprintf "%s/%s/runtime/%s/entity/%s" droot node_uuid handler.uuid manifest.uuid in
  let s = Store.create (sprintf "d%s" home) droot dhome in
  let _ = Store.put s uri (Types_j.string_of_atomic_entity manifest)
  in wait_atomic_entity_state_change node_uuid handler.uuid manifest.uuid "defined"

let send_atomic_entity_remove node_uuid entity_uuid =
  let handler = get_entity_handler_by_uuid node_uuid entity_uuid in
  let uri = sprintf "%s/%s/runtime/%s/entity/%s" droot node_uuid handler entity_uuid in
  let s = Store.create (sprintf "d%s" home) droot dhome in
  Store.remove s uri

let send_atomic_entity_instance_action node_uuid entity_uuid instance_uuid action state =
  let handler = get_entity_handler_by_uuid node_uuid entity_uuid in
  let uri = sprintf "%s/%s/runtime/%s/entity/%s/instance/%s#status=%s" droot node_uuid handler entity_uuid instance_uuid action in
  let s = Store.create (sprintf "d%s" home) droot dhome in
  let _ =  Store.dput s uri None in
  ignore @@ wait_atomic_entity_instance_state_change node_uuid handler entity_uuid instance_uuid state

let send_atomic_entity_instance_remove node_uuid entity_uuid instance_uuid =
  let handler = get_entity_handler_by_uuid node_uuid entity_uuid in
  let uri = sprintf "%s/%s/runtime/%s/entity/%s/instance/%s" droot node_uuid handler entity_uuid instance_uuid in
  let s = Store.create (sprintf "d%s" home) droot dhome in
  Store.remove s uri

let send_migrate_atomic_entity_instance node_uuid entity_uuid instance_uuid destination_uuid = ()


let get_node (component : Types_t.component_type) =
  match component.node with
  | Some s -> s
  | _ -> ""  (* TODO Find the correct node!! *)

let rec dedup xs =
  match xs with
  | hd::tl -> hd :: (dedup @@ List.filter ~f:(fun x -> x <> hd) tl)
  | [] -> []

let dep_graph (n: Types_t.component_type) (g: Types_t.component_type list) =
  let ds = n.need in
  List.filter ~f:(fun x -> List.exists ~f:(fun a -> a = x.name) ds) g

let rec dep_order_wd (dg: Types_t.component_type list) (g: Types_t.component_type list) =
  match dg with
  | hd::tl -> (dep_order_wd (dep_graph hd g) g) @ dep_order_wd tl g @ [hd.name]
  | [] -> []

let dep_order (dg: Types_t.component_type list) = dedup @@ dep_order_wd dg dg

(* TODO check this *)
(* [{'name': 'c1', 'need': ['c2', 'c3']}, {'name': 'c2', 'need': ['c3']}, {'name': 'c3', 'need': ['c4']}, {'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}] *)
let resolve_entity_dependencies (components : Types_t.component_type list) =
  dep_order components
