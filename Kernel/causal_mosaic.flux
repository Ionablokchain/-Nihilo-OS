# causal_mosaic.flux – Expune API pentru operarea mozaicurilor

causal_mosaic system_mosaic = sparse_temporal_matrix();

flow CausalMosaicService {
    execute: {
        while true {
            let req = listen("mosaic", 100ms, "");
            if req == "" { continue; }
            
            # Format: "key:value:weight"
            let parts = split(req, ":");
            if len(parts) >= 2 {
                let key = parts[0];
                let value = parts[1];
                let weight = if len(parts) >= 3 then parse_float(parts[2]) else 1.0;
                system_mosaic.accept(key).write(value, weight);
                send("tactile", "stored", 100ms);
            }
        }
    }
}