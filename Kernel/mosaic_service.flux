// mosaic_service.flux – Serviciu de stocare distribuită (mozaic cauzal)

causal_mosaic system_store = sparse_temporal_matrix();

flow MosaicService {
    execute: {
        while true {
            let cmd = listen("mosaic", 200ms, "");
            if cmd == "" { continue; }
            
            let parts = split(cmd, "|");
            if parts[0] == "write" and len(parts) >= 3 {
                let key = parts[1];
                let value = parts[2];
                let weight = if len(parts) >= 4 then to_float(parts[3]) else 1.0;
                system_store.accept(key).write(value, weight);
                send("tactile", "stored", 200ms);
            }
            else if parts[0] == "read" and len(parts) >= 2 {
                let key = parts[1];
                let val = system_store.accept(key).read() otherwise "<nil>";
                send("inner_voice", key ++ " = " ++ to_string(val), 1s);
            }
            else if parts[0] == "save" {
                save_mosaic("state/mosaic.json");
                send("inner_voice", "Mosaic saved to state/mosaic.json", 1s);
            }
            else if parts[0] == "load" {
                load_mosaic("state/mosaic.json");
                send("inner_voice", "Mosaic loaded from state/mosaic.json", 1s);
            }
            else {
                send("tactile", "Bad mosaic command", 300ms);
            }
        }
    }
}