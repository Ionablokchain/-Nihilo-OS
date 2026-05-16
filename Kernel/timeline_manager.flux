// timeline_manager.flux – Manage timelines: create, list, switch, merge.
//
// Commands (sent via listen("timeline")):
//   create                – create a new timeline (auto‑named)
//   list                  – list all existing timelines
//   switch|<name>         – switch current timeline to <name>
//   merge|<source>        – merge <source> timeline into the current one

causal_mosaic timeline_registry = sparse_temporal_matrix();
causal_mosaic kernel_state = sparse_temporal_matrix();

// -------------------------------------------------------------------
// Helper: get the next timeline counter value
// -------------------------------------------------------------------
function get_next_timeline_id() -> int {
    let current = kernel_state.accept("timeline_counter").read() otherwise 1;
    let next = current + 1;
    kernel_state.accept("timeline_counter").write(next, 1.0);
    return current;  // return the old value for naming
}

// -------------------------------------------------------------------
// Helper: check if a timeline exists
// -------------------------------------------------------------------
function timeline_exists(name: string) -> bool {
    let val = timeline_registry.accept(name).read() otherwise nil;
    return val != nil;
}

// -------------------------------------------------------------------
// TimelineManager service – processes timeline commands
// -------------------------------------------------------------------
flow TimelineManager {
    execute: {
        while true {
            let cmd = listen("timeline", 100ms, "");
            if cmd == "" { continue; }

            let parts = split(cmd, "|");
            if len(parts) == 0 { continue; }

            let command = parts[0];

            // -----------------------------------------------------------------
            // Create: create
            // -----------------------------------------------------------------
            if command == "create" {
                let id = get_next_timeline_id();
                let name = "tl_" + to_string(id);
                create_timeline(name);
                timeline_registry.accept(name).write(now(), 1.0);
                send("inner_voice", "Created timeline: " ++ name, 1s);
            }

            // -----------------------------------------------------------------
            // List: list
            // -----------------------------------------------------------------
            else if command == "list" {
                // Collect all timeline names (simplified – in practice you'd need
                // a way to enumerate keys; here we assume a built‑in `timeline_keys()`
                // or we maintain a separate list in kernel_state).
                // For this example, we maintain a separate list.
                let all = kernel_state.accept("timeline_list").read() otherwise [];
                if len(all) == 0 {
                    send("inner_voice", "No timelines found.", 1s);
                } else {
                    send("mental_image", "Timelines: " ++ to_string(all), 3s);
                }
            }

            // -----------------------------------------------------------------
            // Switch: switch|name
            // -----------------------------------------------------------------
            else if command == "switch" and len(parts) >= 2 {
                let name = parts[1];
                if timeline_exists(name) {
                    set_current_timeline(name);
                    send("inner_voice", "Switched to timeline: " ++ name, 1s);
                } else {
                    send("tactile", "Timeline not found: " ++ name, 1s);
                }
            }

            // -----------------------------------------------------------------
            // Merge: merge|source
            // -----------------------------------------------------------------
            else if command == "merge" and len(parts) >= 2 {
                let src = parts[1];
                let dst = current_timeline();
                if timeline_exists(src) {
                    merge_timelines(src, dst, "keep_target");
                    // Remove from registry after merge
                    timeline_registry.accept(src).delete();
                    send("inner_voice", "Merged " ++ src ++ " into " ++ dst, 1s);
                } else {
                    send("tactile", "Cannot merge: " ++ src ++ " does not exist", 1s);
                }
            }

            // -----------------------------------------------------------------
            // Unknown command
            // -----------------------------------------------------------------
            else {
                send("tactile", "Bad timeline command. Use: create, list, switch|name, merge|name", 2s);
            }

            // Short sleep to prevent busy‑looping
            sleep(50ms);
        }
    }
}
