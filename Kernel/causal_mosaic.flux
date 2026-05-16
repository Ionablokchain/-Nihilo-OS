// causal_mosaic.flux – Service for operating the causal mosaic.
// Provides persistent storage with weighted branches.
// Commands (sent via listen("mosaic")):
//   write|key|value|weight   – store a weighted value (weight optional, default 1.0)
//   read|key                 – retrieve the most probable value for a key
//   save                     – persist entire mosaic to disk (state/mosaic.json)
//   load                     – restore mosaic from disk

causal_mosaic system_mosaic = sparse_temporal_matrix();

// -------------------------------------------------------------------
// CausalMosaicService – infinite loop processing commands on the "mosaic" channel
// -------------------------------------------------------------------

flow CausalMosaicService {
    execute: {
        while true {
            let req = listen("mosaic", 100ms, "");
            if req == "" { continue; }

            let parts = split(req, "|");
            if len(parts) == 0 { continue; }

            let command = parts[0];

            // -----------------------------------------------------------------
            // Write command: write|key|value|weight
            // -----------------------------------------------------------------
            if command == "write" and len(parts) >= 3 {
                let key = parts[1];
                let value = parts[2];
                let weight = if len(parts) >= 4 then to_float(parts[3]) else 1.0;
                system_mosaic.accept(key).write(value, weight);
                send("tactile", "stored", 100ms);
            }

            // -----------------------------------------------------------------
            // Read command: read|key
            // -----------------------------------------------------------------
            else if command == "read" and len(parts) >= 2 {
                let key = parts[1];
                let val = system_mosaic.accept(key).read() otherwise "<nil>";
                send("inner_voice", key ++ " = " ++ to_string(val), 1s);
            }

            // -----------------------------------------------------------------
            // Save command: save
            // -----------------------------------------------------------------
            else if command == "save" {
                save_mosaic("state/mosaic.json");
                send("inner_voice", "Mosaic saved to state/mosaic.json", 1s);
            }

            // -----------------------------------------------------------------
            // Load command: load
            // -----------------------------------------------------------------
            else if command == "load" {
                load_mosaic("state/mosaic.json");
                send("inner_voice", "Mosaic loaded from state/mosaic.json", 1s);
            }

            // -----------------------------------------------------------------
            // Unknown command
            // -----------------------------------------------------------------
            else {
                send("tactile", "Invalid mosaic command", 300ms);
            }
        }
    }
}
