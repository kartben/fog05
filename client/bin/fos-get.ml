let uri = ref "****"

let set_uri u = uri := u

let main = 
  begin
    let speclist = [
      ("-u",Arg.String(set_uri), "URI")
    ]
    in let usage_msg = "Fog05 get helper for Store, available options:"
    in Arg.parse speclist print_endline usage_msg;
    Printf.printf "%s" (Obj.magic uri)
  end

let () = main
