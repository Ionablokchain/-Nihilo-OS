// scheduler.flux – Priority-based intention scheduler.
// Runs intentions according to priority and event triggers.
//
// Registered intentions must have:
//   - priority (float, higher = more important)
//   - trigger() -> bool (optional, defaults to true)
//   - condition() -> bool (optional, defaults to true)
//   - execute() (the body to run)

causal_mosaic kernel_state = sparse_temporal_matrix();

flow Scheduler {
    execute: {
        while true {
            // Retrieve all registered intentions from the kernel state
            let intentions = kernel_state.accept("registered_intentions").read() otherwise [];
            
            // Sort by priority descending (higher priority first)
            let sorted = intentions sort_by priority desc;
            
            var dispatched = false;
            for intent in sorted {
                // Evaluate trigger (if present, otherwise true)
                let trig_ok = if intent.trigger != nil then intent.trigger() else true;
                // Evaluate condition (if present, otherwise true)
                let cond_ok = if intent.condition != nil then intent.condition() else true;
                
                if trig_ok and cond_ok {
                    // Run the intention in a fresh timeline to isolate side effects
                    let original_tl = current_timeline();
                    let work_tl = create_timeline();
                    set_current_timeline(work_tl);
                    
                    intent.execute();
                    
                    // Merge the work timeline back into the original (probabilistic union)
                    merge_timelines(work_tl, original_tl, "probabilistic_union");
                    set_current_timeline(original_tl);
                    
                    dispatched = true;
                    break;  // Only one intention per scheduler tick
                }
            }
            
            // Adaptive sleep: shorter if work was done, longer if idle
            if dispatched {
                sleep(50ms);
            } else {
                sleep(200ms);
            }
        }
    }
}
