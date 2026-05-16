// bootstrap.flux – First intentions executed at boot
// This file starts the Nihilo OS kernel and its essential services.

causal_mosaic kernel_state = sparse_temporal_matrix();

// -------------------------------------------------------------------
// Bootloader – initializes kernel state and launches core services
// -------------------------------------------------------------------

intention Bootloader {
    trigger: on_boot()
    priority: 1.0
    condition: causal_void.exists()
    execute: {
        // Announce boot
        send("inner_voice", "Booting Nihilo OS...", 2s);
        
        // Initialize kernel state in the causal mosaic
        kernel_state.accept("boot_time").write(now(), 1.0);
        kernel_state.accept("timeline_count").write(1, 1.0);
        kernel_state.accept("services_ready").write(false, 1.0);
        
        // Launch core system services (each runs as a background flow)
        launch(Scheduler);           // priority‑based intention scheduler
        launch(TimelineManager);     // timeline creation, switching, merging
        launch(CausalMosaicService); // persistent key‑value store (mosaic)
        
        // Mark services as ready after a short delay
        sleep(500ms);
        kernel_state.accept("services_ready").write(true, 1.0);
        
        // Final ready message
        send("mental_image", "Nihilo OS ready. Type 'help' for commands.", 5s);
    }
}

// -------------------------------------------------------------------
// Scheduler – infinite loop: picks highest‑priority eligible intention
// -------------------------------------------------------------------

flow Scheduler {
    execute: {
        while true {
            let ready = kernel_state.accept("services_ready").read() otherwise false;
            if not ready {
                sleep(100ms);
                continue;
            }
            
            // Get list of registered intentions from kernel state
            let intentions = kernel_state.accept("active_intentions").read() otherwise [];
            
            // Sort by priority (higher first)
            let sorted = intentions sort_by priority desc;
            
            var dispatched = false;
            for intent in sorted {
                // Check trigger (if any) and condition (if any)
                let trig_ok = if intent.trigger != nil then intent.trigger() else true;
                let cond_ok = if intent.condition != nil then intent.condition() else true;
                
                if trig_ok and cond_ok {
                    // Execute in a fresh timeline to isolate side effects
                    let original = current_timeline();
                    let work = create_timeline();
                    set_current_timeline(work);
                    intent.execute();
                    merge_timelines(work, original, "probabilistic_union");
                    set_current_timeline(original);
                    
                    dispatched = true;
                    break; // one intention per scheduler tick
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

// -------------------------------------------------------------------
// TimelineManager – handles timeline creation, listing, switching
// -------------------------------------------------------------------

causal_mosaic timeline_registry = sparse_temporal_matrix();

flow TimelineManager {
    execute: {
        while true {
            let cmd = listen("timeline", 500ms, "");
            if cmd == "" { continue; }
            
            let parts = split(cmd, "|");
            if parts[0] == "create" {
                let new_id = kernel_state.accept("timeline_count").read() otherwise 1;
                let name = "tl_" + to_string(new_id + 1);
                create_timeline(name);
                timeline_registry.accept(name).write(now(), 1.0);
                kernel_state.accept("timeline_count").write(new_id + 1, 1.0);
                send("inner_voice", "Created timeline: " ++ name, 1s);
            }
            else if parts[0] == "list" {
                let all = timeline_registry.accept("all").read() otherwise [];
                send("mental_image", "Timelines: " ++ to_string(all), 5s);
            }
            else if parts[0] == "switch" and len(parts) >= 2 {
                let name = parts[1];
                if timeline_exists(name) {
                    set_current_timeline(name);
                    send("inner_voice", "Switched to timeline: " ++ name, 1s);
                } else {
                    send("tactile", "Timeline not found: " ++ name, 1s);
                }
            }
            else if parts[0] == "merge" and len(parts) >= 2 {
                let src = parts[1];
                let dst = current_timeline();
                if timeline_exists(src) {
                    merge_timelines(src, dst, "keep_target");
                    send("inner_voice", "Merged " ++ src ++ " into " ++ dst, 1s);
                } else {
                    send("tactile", "Cannot merge: " ++ src ++ " does not exist", 1s);
                }
            }
            else {
                send("tactile", "Unknown timeline command", 500ms);
            }
        }
    }
}

// -------------------------------------------------------------------
// CausalMosaicService – persistent key‑value store (mosaic)
// -------------------------------------------------------------------

causal_mosaic system_store = sparse_temporal_matrix();

flow CausalMosaicService {
    execute: {
        while true {
            let req = listen("mosaic", 500ms, "");
            if req == "" { continue; }
            
            let parts = split(req, "|");
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
                send("tactile", "Invalid mosaic command", 300ms);
            }
        }
    }
}
