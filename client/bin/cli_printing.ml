open Printf
open Types_t



let print_network_info (net_info :Types_t.network) node_id =
  printf "+-------------------------------------------------------+\n";
  printf "| UUID : %s\n" net_info.uuid;
  printf "| Name: %s \n" net_info.name;
  printf "| Type: %s \n" net_info.network_type;
  printf "| Node: %s \n" node_id;
  printf "+-------------------------------------------------------+\n"

let print_node_plugin (plugins : Types_t.plugin list) =
  printf "+-----------------------PLUGINS-------------------------+\n";
    for i = 0 to (List.length plugins) -1 do
      let p = List.nth plugins i in
      printf "| Name: %s \t| UUID: %s\t | Type: %s\n" p.name p.uuid p.plugin_type;
      printf "+-------------------------------------------------------+\n";
    done

let print_node_info (node_info: Types_t.node_info) =
  printf "+-------------------------------------------------------+\n";
  printf "| Name: %s \t| UUID: %s\t\n" node_info.name node_info.uuid;
  printf "+-------------------------------------------------------+\n";
  let cpus = node_info.cpu in
  printf "+------------------------CPU----------------------------+\n";
  printf "| Total CPU %d\n" @@ List.length cpus;
  for i = 0 to (List.length cpus) - 1 do
    printf "+-------------------------------------------------------+\n";
    printf "| ARCH: %s\n" @@ (List.nth cpus i).arch;
    printf "| Model: %s\n" @@ (List.nth cpus i).model;
    printf "| Frequency: %f\n" @@ (List.nth cpus i).frequency;
  done;
  printf "+-------------------------------------------------------+\n";
  let ram = node_info.ram in
  printf "| RAM: %f\n" ram.size;
  printf "+----------------------NETWORKS-------------------------+\n";
  let networks = node_info.network in
  for i = 0 to (List.length networks) - 1 do
    let intf_conf = (List.nth networks i).intf_configuration in
    printf "| Interface: %s\n" (List.nth networks i).intf_name;
    printf "| MAC: %s \n" (List.nth networks i).intf_mac_address;
    printf "| type: %s\n" (List.nth networks i).intf_type;
    printf "| Default gateway: %b \n" (List.nth networks i).default_gw;
    printf "| Speed: %d\n" (List.nth networks i).intf_speed;
    printf "| IPV4: %s Netmask: %s Gateway: %s\n" intf_conf.ipv4_address intf_conf.ipv4_netmask  intf_conf.ipv4_gateway;
    printf "+-------------------------------------------------------+\n";
  done;
  let acc = node_info.accelerator in
  for i = 0 to (List.length acc) - 1 do
    printf "| Name: %s\n" (List.nth acc i).name;
    printf "| HW Address: %s \n" (List.nth acc i).hw_address;
    (* printf "| Supported libraries: %s\n" String.concat @@ (List.nth acc i).supported_library; *)
    printf "+-------------------------------------------------------+\n";
  done;
  let ios = node_info.io in
  for i = 0 to (List.length ios) - 1 do
    printf "| Name: %s\n" (List.nth ios i).name;
    printf "| Type: %s \n" (List.nth ios i).io_type;
    printf "| File: %s\n" (List.nth ios i).io_file;
    printf "+-------------------------------------------------------+\n";
  done;
