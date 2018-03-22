open Core
open Printf
(* open String *)
open Types_t

(*   ignore @@ initialize (); *)
(* >outfile 2> errfile & echo $! > pid file *)
(* "-p"; "9876"; *)
let check s =
  let n = String.length s in
  if n > 0 && s.[n-1] = '\n' then
    String.sub s 0 (n-1)
  else
    s

let initialize =
  let tmp = Filename.temp_dir_name in
  let server_file = Filename.concat tmp "dstore_server.pid" in
  let server_out = Filename.concat tmp "dstore_server.out" in
  let server_err = Filename.concat tmp "dstore_server.err" in
  match Sys.file_exists server_file with
  | `Yes ->
    let pid = int_of_string @@ check @@ Cli_helper.read_file server_file in
    let cmd = sprintf "fos-check-pid %d" pid in
    let channels = Unix.open_process_full cmd ~env:[||] in
    let res = int_of_string @@ check @@ Stdio.In_channel.input_all channels.stdout in
    if res = 0 then let cmd = sprintf "f05ws -p 9876 > %s 2> %s & echo $! > %s" server_out server_err server_file in let _ =  Unix.system cmd in ()
  (* How I can check if the PID still exists? Sending kill 0 <pid>  *)
  | `No ->
    let cmd = sprintf "f05ws -p 9876 > %s 2> %s & echo $! > %s" server_out server_err server_file in
    let _ =  Unix.system cmd in
    let pid = Int.of_string @@ check @@ Cli_helper.read_file server_file in ()
  | `Unknown ->   printf "creating the process"
  ;
  ignore @@ Lwt_unix.sleep 0.3


(* AGENT CMD  *)
let agent =
  Command.basic_spec ~summary:"Agent control"
    Command.Spec.
      (empty
       (* +> flag "start" (no_arg) ~doc:"Sets some flag" *)
       +> flag "-v" (no_arg) ~doc:"Verbose output"
       +> flag "-p" (optional_with_default "" string) ~doc:"plugin path"
       +> flag "-d" (no_arg) ~doc:"Run as a daemon"
      )
    (fun verbose_flag plugin_path daemon_flag () ->
       printf "%b '%s' %b\n" verbose_flag plugin_path daemon_flag
    )

(* NODE CMD *)

let node_list =
  Command.basic_spec ~summary:"List of all available nodes"
    Command.Spec.(empty)
    (fun () ->
       printf "Node list\n";
       printf "+---------------------------------------------+\n";
       let nodes = Cli_helper.get_all_nodes () in
       for i = (List.length nodes)-1 downto 0 do
         match List.nth_exn nodes i with
         | (k, v) ->
           let node_info = Types_j.node_info_of_string v in
           printf "UUID: %s \t Name: %s\n" node_info.uuid node_info.name;
         | _ -> ()
       done;
       printf "+---------------------------------------------+\n";
    )

let node_info =
  Command.basic_spec ~summary:"All info about a node"
    Command.Spec.
      (empty
       +> flag "-u" (required string) ~doc:"Node uuid"
      )
    (fun node_uuid () ->
       printf "Node info\n";
       let s = Store.create (sprintf "a%s" Cli_helper.home) Cli_helper.aroot Cli_helper.ahome in
       let res = Store.get s (sprintf "%s/%s" Cli_helper.aroot node_uuid) in
       match res with
       | k,v -> let node_info = Types_j.node_info_of_string v in
         Cli_printing.print_node_info node_info
       | _ -> ()
    )

let node_plugin_list =
  Command.basic_spec ~summary:"Listing plugin in a node"
    Command.Spec.
      (empty
       +> flag "-u" (required string) ~doc:"Node uuid"
      )
    (fun node_uuid () ->
       Cli_printing.print_node_plugin @@ Cli_helper.get_all_node_plugin node_uuid
    )


let node_plugin_add =
  Command.basic_spec ~summary:"Listing plugin in a node"
    Command.Spec.
      (empty
       +> flag "-u" (required string) ~doc:"Node uuid"
       +> flag "-m" (required string) ~doc:"Path to node manifest"
      )
    (fun node_uuid path () ->
       let cont = Cli_helper.read_file path in
       let res = Cli_helper.check_manifest cont Types_j.plugin_of_string Types_v.validate_plugin  in
       match res with
       | Ok _ -> let plugin = {(Cli_helper.load_manifest cont Types_j.plugin_of_string) with status = Some "add"} in
         let s = Store.create (sprintf "d%s" Cli_helper.home) Cli_helper.droot Cli_helper.dhome in
         let v = Some (Types_j.string_of_plugins_info_type {plugins = [plugin]}) in
         let res = Store.dput s (sprintf "%s/%s/plugins" Cli_helper.droot node_uuid)  v in
         printf "Plugin added\n"
       | Error e -> printf "Manifest has errors: %s\n" (Exn.to_string e)
       | Error _ -> failwith "Deep error"
    )

let node_plugin_remove =
  Command.basic_spec ~summary:"Listing plugin in a node"
    Command.Spec.
      (empty
       +> flag "-u" (required string) ~doc:"Node uuid"
       +> flag "-pu" (required string) ~doc:"Plugin uuid"
      )
    (fun node_uuid plugin_uuid () ->
       printf "Removing: %s  from node: %s\nNot yet available\n" plugin_uuid node_uuid
    )

let node_plugin =
  Command.group ~summary:"Action on plugin for a node"
    ["list",node_plugin_list;"add",node_plugin_add;"remove",node_plugin_remove]

let node =
  Command.group ~summary:"Getting information about nodes"
    ["list",node_list;"info",node_info;"plugin",node_plugin]

(* NETWORK CMD *)

let network_list =
  Command.basic_spec ~summary:"List all network in a node or in the system"
    Command.Spec.
      (empty
       +> flag "-u" (optional_with_default "" string) ~doc:"Node uuid"
      )
    (fun node_uuid () ->
       match node_uuid with
       | "" -> let s = Store.create (sprintf "a%s" Cli_helper.home) Cli_helper.aroot Cli_helper.ahome in
         let res = Store.resolve_all s (sprintf "%s/*/network/*/networks/*" Cli_helper.aroot) in
         for i = (List.length res)-1 downto 0 do
           match List.nth_exn res i with
           | (k, v) ->
             let net_info = Types_j.network_of_string v in
             Cli_printing.print_network_info net_info (List.nth_exn (String.split k ~on:'/') 4)
         done
       | _ -> printf "Listing network in node %s\n" node_uuid

    )

let network_add =
  Command.basic_spec ~summary:"Adding a network"
    Command.Spec.(
      empty
      +> flag "-u" (optional_with_default "" string) ~doc:"Node uuid"
      +> flag "-m" (required string) ~doc:"Path to network manifest"
    )
    (fun node_uuid path () ->
       match node_uuid with
       | "" -> printf "Adding network from %s to all nodes not yet\n" path
       | _ -> printf "Adding network from %s to node  %s\n" path node_uuid;
         let cont = Cli_helper.read_file path in
         let res = Cli_helper.check_manifest cont Types_j.network_of_string Types_v.validate_network  in
         match res with
         | Ok _ -> ignore @@ Cli_helper.send_add_network_node (Types_j.network_of_string cont) node_uuid
         | Error e -> printf "Error in manifest %s\n" (Exn.to_string e)

    )

let network_remove =
  Command.basic_spec ~summary:"Removing a network"
    Command.Spec.(
      empty
      +> flag "-u" (optional_with_default "" string) ~doc:"Node uuid"
      +> flag "-nu" (required string) ~doc:"Network uuid"
    )
    (fun node_uuid net_uuid () ->
       match node_uuid with
       | "" -> printf "Removing network %s from all nodes not yet\n" net_uuid
       | _ -> Cli_helper.send_remove_network_node net_uuid node_uuid;
         printf "Removed network %s from node  %s\n" net_uuid node_uuid
    )

let network =
  Command.group ~summary:"Network related commands"
    ["list",network_list;"add",network_add;"remove",network_remove]

(* MANIFEST CMD *)


let manifest_network =
  Command.basic_spec ~summary:"Check network manifest"
    Command.Spec.(
      empty
      +> flag "-m" (required string) ~doc:"Path to network manifest"
    )
    (fun path () ->
       printf "Check manifest %s\n" path;
       let cont = Cli_helper.read_file path in
       let res = Cli_helper.check_manifest cont Types_j.network_of_string Types_v.validate_network  in
       match res with
       | Ok _ -> printf "Manifest is Ok\n"
       | Error e -> printf "Manifest has errors: %s\n" (Exn.to_string e)

    )


let manifest_aentity =
  Command.basic_spec ~summary:"Check atomic entity manifest"
    Command.Spec.(
      empty
      +> flag "-m" (required string) ~doc:"Path to atomic entity manifest"
    )
    (fun path () ->
       printf "Check manifest %s\n" path;
       let cont = Cli_helper.read_file path in
       let res = Cli_helper.check_manifest cont Types_j.atomic_entity_of_string Types_v.validate_atomic_entity  in
       match res with
       | Ok _ -> printf "Manifest is Ok\n"
       | Error e -> printf "Manifest has errors: %s\n" (Exn.to_string e)
    )

let manifest_entity =
  Command.basic_spec ~summary:"Check entity manifest"
    Command.Spec.(
      empty
      +> flag "-m" (required string) ~doc:"Path to entity manifest"
    )
    (fun path () ->
       printf "Check manifest %s\n" path;
       let cont = Cli_helper.read_file path in
       let res = Cli_helper.check_manifest cont Types_j.entity_of_string Types_v.validate_entity  in
       match res with
       | Ok _ -> printf "Manifest is Ok\n"
       | Error e -> printf "Manifest has errors: %s\n" (Exn.to_string e)
    )


let manifest_plugin =
  Command.basic_spec ~summary:"Check plugin manifest"
    Command.Spec.(
      empty
      +> flag "-m" (required string) ~doc:"Path to plugin manifest"
    )
    (fun path () ->
       printf "Check manifest %s\n" path;
       let cont = Cli_helper.read_file path in
       let res = Cli_helper.check_manifest cont Types_j.plugin_of_string Types_v.validate_plugin  in
       match res with
       | Ok _ -> printf "Manifest is Ok\n"
       | Error e -> printf "Manifest has errors: %s\n" (Exn.to_string e)
    )

let manifest_flavor =
  Command.basic_spec ~summary:"Check flavor manifest"
    Command.Spec.(
      empty
      +> flag "-m" (required string) ~doc:"Path to flavor manifest"
    )
    (fun path () ->
       printf "Check manifest %s\n" path;
       let cont = Cli_helper.read_file path in
       let res = Cli_helper.check_manifest cont Types_j.flavor_of_string Types_v.validate_flavor  in
       match res with
       | Ok _ -> printf "Manifest is Ok\n"
       | Error e -> printf "Manifest has errors: %s\n" (Exn.to_string e)
    )

let manifest_image =
  Command.basic_spec ~summary:"Check image manifest"
    Command.Spec.(
      empty
      +> flag "-m" (required string) ~doc:"Path to image manifest"
    )
    (fun path () ->
       printf "Check manifest %s\n" path;
       let cont = Cli_helper.read_file path in
       let res = Cli_helper.check_manifest cont Types_j.image_of_string Types_v.validate_image  in
       match res with
       | Ok _ -> printf "Manifest is Ok\n"
       | Error e -> printf "Manifest has errors: %s\n" (Exn.to_string e)
    )

let manifest =
  Command.group ~summary:"Check manifests"
    ["network",manifest_network;"aentity",manifest_aentity;"entity",manifest_entity;"plugin",manifest_plugin;"flavor",manifest_flavor;"image",manifest_image]


(* ENTITY CMD *)


let entity_add =
  Command.basic_spec ~summary:"Onboard Entity or Atomic Entity"
    Command.Spec.(
      empty
      +> flag "-m" (required string) ~doc:"Path to entity/atomic entity manifest"
    )
    (fun path () ->
       printf "Onboarding from manifest %s\n" path;
       let cont = Cli_helper.read_file path in
       let res = Cli_helper.check_manifest cont Types_j.entity_of_string Types_v.validate_entity  in
       match res with
       | Ok _ ->  let entity = Cli_helper.load_manifest cont Types_j.entity_of_string in
         let deps = Cli_helper.resolve_entity_dependencies entity.components in
         let nodes = Cli_helper.get_all_nodes_uuid () in
         let nws = match entity.networks with
           | Some l -> l
           | None -> []
         in
         List.iteri nws ~f:(fun i e -> List.iteri nodes ~f:(fun i n -> ignore @@ Cli_helper.send_add_network_node e n));
         let uuids = List.map deps ~f:(fun e ->
             let m = List.find_exn entity.components ~f:(fun c -> c.name=e) in
             let instance_uuid = Uuid.to_string_hum (Uuid.create () ) in
             let node = Cli_helper.get_node m in
             ignore @@ Cli_helper.send_atomic_entity_define m.manifest node;
             ignore @@ Cli_helper.send_atomic_entity_instance_action node m.manifest.uuid instance_uuid "configure" "configured";
             ignore @@ Cli_helper.send_atomic_entity_instance_action node m.manifest.uuid instance_uuid "run" "run";
             instance_uuid
           ) in
         printf "Onboarded:\n";
         List.iteri uuids ~f:(fun i e -> printf "%s\n" e)
       | Error e -> printf "Manifest has errors: %s\n" (Exn.to_string e)
    )

let entity_remove =
  Command.basic_spec ~summary:"Offloading Entity or Atomic Entity"
    Command.Spec.(
      empty
      +> flag "-eu" (required string) ~doc:"Entity or Atomic Entity uuid "
    )
    (fun entity_uuid () ->
       printf "Offloading %s from the system not yet" entity_uuid
    )

let entity_define =
  Command.basic_spec ~summary:"Define Atomic Entity"
    Command.Spec.(
      empty
      +> flag "-u" (required string) ~doc:"Node uuid"
      +> flag "-m" (required string) ~doc:"Path to atomic entity manifest"
    )
    (fun node_uuid path () ->
       printf "Define entity from %s to node %s" path node_uuid;
       let cont = Cli_helper.read_file path in
       let res = Cli_helper.check_manifest cont Types_j.atomic_entity_of_string Types_v.validate_atomic_entity  in
       match res with
       | Ok _ ->  let manifest = Cli_helper.load_manifest cont Types_j.atomic_entity_of_string in
         Cli_helper.send_atomic_entity_define manifest node_uuid;
         printf "Atomic Entity Defined\n";
       | Error e -> printf "Manifest has errors: %s\n" (Exn.to_string e)
    )

let entity_undefine =
  Command.basic_spec ~summary:"Undefine Atomic Entity"
    Command.Spec.(
      empty
      +> flag "-u" (required string) ~doc:"Node uuid"
      +> flag "-eu" (required string) ~doc:"Atomic Entity uuid"
    )
    (fun node_uuid entity_uuid () ->
       printf "Undefine entity %s from node %s" entity_uuid node_uuid;
       Cli_helper.send_atomic_entity_remove node_uuid entity_uuid;
       printf "Atomic Entity Removed\n";

    )

let entity_configure =
  Command.basic_spec ~summary:"Configure Atomic Entity"
    Command.Spec.(
      empty
      +> flag "-u" (required string) ~doc:"Node uuid"
      +> flag "-eu" (required string) ~doc:"Atomic Entity uuid"
      +> flag "-iu" (required string) ~doc:"Instance uuid"
    )
    (fun node_uuid entity_uuid instance_uuid () ->
       printf "Configure entity %s with instance %s to node %s\n" entity_uuid instance_uuid node_uuid;
       Cli_helper.send_atomic_entity_instance_action node_uuid entity_uuid instance_uuid "configure" "configured";
       printf "Atomic Entity Configured\n";
    )

let entity_clean =
  Command.basic_spec ~summary:"Clean Atomic Entity"
    Command.Spec.(
      empty
      +> flag "-u" (required string) ~doc:"Node uuid"
      +> flag "-eu" (required string) ~doc:"Atomic Entity uuid"
      +> flag "-iu" (required string) ~doc:"Instance uuid"
    )
    (fun node_uuid entity_uuid instance_uuid () ->
       printf "Clean instance %s entity %s from node %s\n" instance_uuid entity_uuid node_uuid;
       Cli_helper.send_atomic_entity_instance_remove node_uuid entity_uuid instance_uuid ;
       printf "Atomic Entity Cleaned\n";
    )

let entity_run =
  Command.basic_spec ~summary:"Run Atomic Entity"
    Command.Spec.(
      empty
      +> flag "-u" (required string) ~doc:"Node uuid"
      +> flag "-eu" (required string) ~doc:"Atomic Entity uuid"
      +> flag "-iu" (required string) ~doc:"Instance uuid"
    )
    (fun node_uuid entity_uuid instance_uuid () ->
       printf "Run entity %s with instance %s to node %s\n" entity_uuid instance_uuid node_uuid;
       Cli_helper.send_atomic_entity_instance_action node_uuid entity_uuid instance_uuid "run" "run";
       printf "Atomic Entity Running\n";
    )

let entity_stop =
  Command.basic_spec ~summary:"Stop Atomic Entity"
    Command.Spec.(
      empty
      +> flag "-u" (required string) ~doc:"Node uuid"
      +> flag "-eu" (required string) ~doc:"Atomic Entity uuid"
      +> flag "-iu" (required string) ~doc:"Instance uuid"
    )
    (fun node_uuid entity_uuid instance_uuid () ->
       printf "Stop entity %s with instance %s to node %s" entity_uuid instance_uuid node_uuid;
       Cli_helper.send_atomic_entity_instance_action node_uuid entity_uuid instance_uuid "stop" "stop";
       printf "Atomic Entity Stopped\n";
    )

let entity_pause =
  Command.basic_spec ~summary:"Pause Atomic Entity"
    Command.Spec.(
      empty
      +> flag "-u" (required string) ~doc:"Node uuid"
      +> flag "-eu" (required string) ~doc:"Atomic Entity uuid"
      +> flag "-iu" (required string) ~doc:"Instance uuid"
    )
    (fun node_uuid entity_uuid instance_uuid () ->
       printf "Pause entity %s with instance %s to node %s" entity_uuid instance_uuid node_uuid;
       Cli_helper.send_atomic_entity_instance_action node_uuid entity_uuid instance_uuid "pause" "pause";
       printf "Atomic Entity Paused\n";
    )

let entity_resume =
  Command.basic_spec ~summary:"Resume Atomic Entity"
    Command.Spec.(
      empty
      +> flag "-u" (required string) ~doc:"Node uuid"
      +> flag "-eu" (required string) ~doc:"Atomic Entity uuid"
      +> flag "-iu" (required string) ~doc:"Instance uuid"
    )
    (fun node_uuid entity_uuid instance_uuid () ->
       printf "Resume entity %s with instance %s to node %s" entity_uuid instance_uuid node_uuid;
       Cli_helper.send_atomic_entity_instance_action node_uuid entity_uuid instance_uuid "resume" "run";
       printf "Atomic Entity Running\n";
    )

let entity_migrate =
  Command.basic_spec ~summary:"Migrate Atomic Entity"
    Command.Spec.(
      empty
      +> flag "-u" (required string) ~doc:"Node uuid"
      +> flag "-eu" (required string) ~doc:"Atomic Entity uuid"
      +> flag "-iu" (required string) ~doc:"Instance uuid"
      +> flag "-du" (required string) ~doc:"Destination node uuid"
    )
    (fun node_uuid entity_uuid instance_uuid destination_node () ->
       printf "Migrate entity %s with instance %s from node %s to node %s" entity_uuid instance_uuid node_uuid destination_node
    )


let entity =
  Command.group ~summary:"Entity/Atomic Entity interaction"
    ["add",entity_add;"remove",entity_remove;"define",entity_define;"undefine",entity_undefine;"configure",entity_configure;"clean",entity_clean;"run",entity_run;"stop",entity_stop;"pause",entity_pause;"resume",entity_resume;"migrate",entity_migrate]

(* CMD *)

let command =
  Command.group  ~summary:"fog05 | The Fog-Computing IaaS"
    ["start",agent;"node",node;"network", network;"entity",entity;"manifest",manifest]

let () =
  Command.run command
