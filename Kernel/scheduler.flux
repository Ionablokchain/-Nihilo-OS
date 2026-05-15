# scheduler.flux – Rulează intenții în funcție de prioritate și evenimente

causal_mosaic intention_queue = sparse_temporal_matrix();

flow Scheduler {
    execute: {
        while true {
            # Colectează toate intențiile active (înregistrate în mosaic)
            let intentions = kernel_state.accept("registered_intentions").read() otherwise [];
            
            # Sortează descrescător după prioritate
            let sorted = intentions sort_by priority desc;
            
            for intent in sorted {
                # Verifică trigger-ul și condiția (evaluate de VM)
                if intent.trigger() and intent.condition() {
                    # Rulează intenția într-un timeline separat
                    let tl = create_timeline();
                    set_current_timeline(tl);
                    intent.execute();
                    merge_timelines(tl, current_timeline(), "probabilistic_union");
                }
            }
            
            # Pauză scurtă pentru a nu consuma toată energia cauzală
            sleep(100ms);
        }
    }
}