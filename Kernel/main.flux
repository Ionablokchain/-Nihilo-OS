// main.flux – Nihilo OS kernel entry point
// This file implements the complete OS in Flux.
// Run with: fluxc main.flux --run

// -------------------------------------------------------------------
// 1. Global kernel state (causal mosaic)
// -------------------------------------------------------------------

causal_mosaic kernel_state = sparse_temporal_matrix();
causal_mosaic persistent_store = sparse_temporal_matrix();

// -------------------------------------------------------------------
// 2. Boot intention – runs once at startup
// -------------------------------------------------------------------

intention Boot {
    trigger: on_boot()
    priority: 1.0
    condition: causal_void.exists()
    execute: {
        // Load persistent mosaic from disk (if exists)
        let loaded = load_mosaic("state/persistent.json");
        if loaded {
            send("inner_voice", "Loaded previous state.", 1s);
        } else {
            send("inner_voice", "Fresh boot – no previous state found.", 1s);
        }

        // Initialize kernel metadata
        kernel_state.accept("boot_time").write(now(), 1.0);
        kernel_state.accept("active_intentions").write([], 1.0);
        kernel_state.accept("timeline_counter").write(1, 1.0);
        kernel_state.accept("scheduler_running").write(true, 1.0);

        send("mental_image", "Nihilo OS – Boot complete. Type 'help' for commands.", 4s);
    }
}

// -------------------------------------------------------------------
// 3. Scheduler – infinite loop that runs intentions by priority
// -------------------------------------------------------------------

flow Scheduler {
    execute: {
        while true {
            let running = kernel_state.accept("scheduler_running").read() otherwise true;
            if not running { break; }

            // Get list of all intentions from kernel_state
            let intentions = kernel_state.accept("active_intentions").read() otherwise [];

            // Sort by priority descending (priority is stored per intention)
            let sorted = intentions sort_by priority desc;

            var dispatched = false;
            for intent in sorted {
                // Evaluate trigger and condition (both optional)
                let trig_ok = if intent.trigger != nil then intent.trigger() else true;
                let cond_ok = if intent.condition != nil then intent.condition() else true;

                if trig_ok and cond_ok {
                    // Execute in a fresh timeline
                    let orig_tl = current_timeline();
                    let work_tl = create_timeline();
                    set_current_timeline(work_tl);
                    intent.execute();
                    // Merge changes back
                    merge_timelines(work_tl, orig_tl, "probabilistic_union");
                    set_current_timeline(orig_tl);

                    dispatched = true;
                    break;  // one intention per scheduler tick
                }
            }

            // Adaptive sleep: if nothing ran, wait longer
            if dispatched {
                sleep(50ms);
            } else {
                sleep(200ms);
            }
        }
    }
}

// -------------------------------------------------------------------
// 4. Mosaic service – handles persistent storage commands
// -------------------------------------------------------------------

flow MosaicService {
    execute: {
        while true {
            let cmd = listen("mosaic", 500ms, "");
            if cmd == "" { continue; }

            let parts = split(cmd, "|");
            if parts[0] == "write" and len(parts) >= 3 {
                let key = parts[1];
                let value = parts[2];
                let weight = if len(parts) >= 4 then to_float(parts[3]) else 1.0;
                persistent_store.accept(key).write(value, weight);
                send("tactile", "stored", 200ms);
            }
            else if parts[0] == "read" and len(parts) >= 2 {
                let key = parts[1];
                let val = persistent_store.accept(key).read() otherwise "<nil>";
                send("inner_voice", key ++ " = " ++ to_string(val), 1s);
            }
            else if parts[0] == "save" {
                save_mosaic("state/persistent.json");
                send("inner_voice", "State saved.", 1s);
            }
            else if parts[0] == "load" {
                load_mosaic("state/persistent.json");
                send("inner_voice", "State loaded.", 1s);
            }
            else {
                send("tactile", "Bad mosaic command", 300ms);
            }
        }
    }
}

// -------------------------------------------------------------------
// 5. Paradox engine – authentication via temporal puzzles
// -------------------------------------------------------------------

causal_mosaic paradox_db = sparse_temporal_matrix();

function generate_challenge(user: string) -> string {
    let seed = now() as int;
    let length = 3;
    let p = generate_paradox("prime_interval", seed, length, 0);
    paradox_db.accept(user).write(p, 1.0);
    return to_string(p);
}

function verify_challenge(user: string, response: string) -> bool {
    let stored = paradox_db.accept(user).read() otherwise "";
    return response == stored;
}

flow ParadoxEngine {
    execute: {
        while true {
            let req = listen("paradox", 1s, "");
            if req == "" { continue; }

            let parts = split(req, "|");
            if parts[0] == "challenge" {
                let user = if len(parts) >= 2 then parts[1] else "anonymous";
                let code = generate_challenge(user);
                send("inner_voice", "Paradox challenge: " ++ code, 4s);

                let response = listen(user, 15s, "");
                if verify_challenge(user, response) {
                    send("mental_image", "✅ Authentication successful.", 2s);
                    kernel_state.accept("auth_" ++ user).write(true, 1.0);
                } else {
                    send("tactile", "❌ Failed. Timeline reset.", 1s);
                    reset_timeline(user);
                }
            }
            else if parts[0] == "resolve" {
                let p = listen("paradox_input", 5s, "");
                let result = resolve_paradox(p, "multicollapse_with_humor");
                send("inner_voice", "Resolved paradox: " ++ to_string(result), 1s);
            }
        }
    }
}

// -------------------------------------------------------------------
// 6. Shell – interactive user interface (REPL)
// -------------------------------------------------------------------

flow Shell {
    execute: {
        while true {
            let cmd = listen(user, 30s, "");
            if cmd == "" { continue; }

            if cmd == "help" {
                send("mental_image",
                     "=== Nihilo OS Commands ===\n"
                     "  status                – show system info\n"
                     "  timeline list         – list all timelines\n"
                     "  timeline new          – create new timeline\n"
                     "  timeline switch <n>   – change timeline\n"
                     "  mosaic write k v [w]  – store weighted value\n"
                     "  mosaic read k         – retrieve most probable\n"
                     "  mosaic save           – persist data\n"
                     "  mosaic load           – restore data\n"
                     "  paradox challenge     – authenticate\n"
                     "  exit                  – shutdown OS",
                     15s);
            }
            else if cmd == "status" {
                let boot = kernel_state.accept("boot_time").read() otherwise "unknown";
                let tl = current_timeline();
                let auth = kernel_state.accept("auth_user").read() otherwise "not authenticated";
                send("inner_voice",
                     "Boot time: " ++ to_string(boot) ++ "\n" ++
                     "Timeline: " ++ tl ++ "\n" ++
                     "Auth: " ++ to_string(auth),
                     4s);
            }
            else if cmd starts_with "mosaic write " {
                let rest = substring(cmd, 13);
                let parts = split(rest, " ");
                if len(parts) >= 2 {
                    let key = parts[0];
                    let val = parts[1];
                    let w = if len(parts) >= 3 then to_float(parts[2]) else 1.0;
                    launch(MosaicService, "write|" ++ key ++ "|" ++ val ++ "|" ++ to_string(w));
                } else {
                    send("tactile", "Usage: mosaic write <key> <value> [weight]", 1s);
                }
            }
            else if cmd starts_with "mosaic read " {
                let key = substring(cmd, 12);
                launch(MosaicService, "read|" ++ key);
            }
            else if cmd == "mosaic save" {
                launch(MosaicService, "save");
            }
            else if cmd == "mosaic load" {
                launch(MosaicService, "load");
            }
            else if cmd == "paradox challenge" {
                launch(ParadoxEngine, "challenge|user");
            }
            else if cmd == "timeline list" {
                let all = list_timelines();
                send("mental_image", "Active timelines: " ++ to_string(all), 5s);
            }
            else if cmd == "timeline new" {
                let new_tl = create_timeline();
                send("inner_voice", "Created timeline: " ++ new_tl, 1s);
            }
            else if cmd starts_with "timeline switch " {
                let name = substring(cmd, 17);
                if timeline_exists(name) {
                    set_current_timeline(name);
                    send("inner_voice", "Switched to timeline: " ++ name, 1s);
                } else {
                    send("tactile", "Timeline not found: " ++ name, 1s);
                }
            }
            else if cmd == "exit" {
                send("inner_voice", "Saving state and shutting down...", 1s);
                save_mosaic("state/persistent.json");
                kernel_state.accept("scheduler_running").write(false, 1.0);
                send("mental_image", "Goodbye.", 1s);
                exit();
            }
            else {
                send("tactile", "Unknown command. Type 'help'.", 1s);
            }
        }
    }
}

// -------------------------------------------------------------------
// 7. Main – launch everything and keep the system alive
// -------------------------------------------------------------------

intention Main {
    trigger: on_boot()
    priority: 1.0
    execute: {
        // Register all intentions with the kernel state
        let all_intentions = [
            { name: "Boot", priority: 1.0, trigger: nil, condition: nil, execute: nil },
            { name: "Scheduler", priority: 0.9, trigger: nil, condition: nil, execute: nil },
            { name: "MosaicService", priority: 0.8, trigger: nil, condition: nil, execute: nil },
            { name: "ParadoxEngine", priority: 0.7, trigger: nil, condition: nil, execute: nil },
            { name: "Shell", priority: 0.6, trigger: nil, condition: nil, execute: nil }
        ];
        kernel_state.accept("active_intentions").write(all_intentions, 1.0);

        // Launch each service as a flow (they run in background)
        launch(Boot);
        launch(Scheduler);
        launch(MosaicService);
        launch(ParadoxEngine);
        launch(Shell);

        // The main intention stays alive, letting the scheduler run forever
        suspend_until_exit();
    }
}
