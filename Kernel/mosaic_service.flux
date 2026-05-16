// mosaic_service.flux – Distributed storage service (causal mosaic)
// Provides persistent, weighted key‑value storage across timelines.
//
// Commands (sent via listen("mosaic")):
//   write|key|value|weight   – store a weighted value (weight optional, default 1.0)
//   read|key                 – retrieve the most probable value for a key
//   list                     – show all keys currently stored
//   delete|key               – remove a key and all its branches
//   save                     – persist entire mosaic to disk (state/mosaic.json)
//   load                     – restore mosaic from disk

causal_mosaic system_store = sparse_temporal_matrix();

flow MosaicService {
    execute: {
        while true {
            let cmd = listen("mosaic", 200ms, "");
            if cmd == "" { continue; }

            let parts = split(cmd, "|");
            if len(parts) == 0 { continue; }

            let command = parts[0];

            // -----------------------------------------------------------------
            // Write: write|key|value|weight
            // -----------------------------------------------------------------
            if command == "write" and len(parts) >= 3 {
                let key = parts[1];
                let value = parts[2];
                let weight = if len(parts) >= 4 then to_float(parts[3]) else 1.0;
                system_store.accept(key).write(value, weight);
                send("tactile", "stored", 200ms);
            }

            // -----------------------------------------------------------------
            // Read: read|key
            // -----------------------------------------------------------------
            else if command == "read" and len(parts) >= 2 {
                let key = parts[1];
                let val = system_store.accept(key).read() otherwise "<nil>";
                send("inner_voice", key ++ " = " ++ to_string(val), 1s);
            }

            // -----------------------------------------------------------------
            // List: list
            // -----------------------------------------------------------------
            else if command == "list" {
                // Retrieve all keys (implementation depends on mosaic capabilities)
                // For this example, we assume a built‑in `mosaic_keys()` exists.
                // If not, you can maintain a separate key list in kernel_state.
                let keys = system_store.keys() otherwise [];
                send("mental_image", "Mosaic keys: " ++ to_string(keys), 3s);
            }

            // -----------------------------------------------------------------
            // Delete: delete|key
            // -----------------------------------------------------------------
            else if command == "delete" and len(parts) >= 2 {
                let key = parts[1];
                system_store.accept(key).delete();
                send("tactile", "deleted", 200ms);
            }

            // -----------------------------------------------------------------
            // Save: save
            // -----------------------------------------------------------------
            else if command == "save" {
                save_mosaic("state/mosaic.json");
                send("inner_voice", "Mosaic saved to state/mosaic.json", 1s);
            }

            // -----------------------------------------------------------------
            // Load: load
            // -----------------------------------------------------------------
            else if command == "load" {
                load_mosaic("state/mosaic.json");
                send("inner_voice", "Mosaic loaded from state/mosaic.json", 1s);
            }

            // -----------------------------------------------------------------
            // Unknown command
            // -----------------------------------------------------------------
            else {
                send("tactile", "Bad mosaic command", 300ms);
            }
        }
    }
}
