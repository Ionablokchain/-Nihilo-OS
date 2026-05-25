// shell.flux – Interactive user shell for Nihilo OS
// Listens for user commands and dispatches them to appropriate services.
// Commands: help, status, timeline, mosaic, paradox, collapse, exit.

causal_mosaic kernel_state = sparse_temporal_matrix();
causal_mosaic system_mosaic = sparse_temporal_matrix();

// ------------------------------------------------------------------
// Helper: split command line into arguments (respecting quotes)
// ------------------------------------------------------------------
function parse_command(line: string) -> [string] {
    let args = [];
    let current = "";
    let in_quote = false;
    for i in 0..len(line) {
        let ch = line[i];
        if ch == '"' {
            in_quote = not in_quote;
        } else if ch == ' ' and not in_quote {
            if current != "" {
                args = append(args, current);
                current = "";
            }
        } else {
            current = current + ch;
        }
    }
    if current != "" {
        args = append(args, current);
    }
    args
}

// ------------------------------------------------------------------
// Main shell intention – runs repeatedly
// ------------------------------------------------------------------
intention Shell {
    trigger: on_user_intention()
    priority: 0.8
    condition: kernel_state.accept("services_ready").read() otherwise false
    execute: {
        let raw = listen("user", 30s, "");
        if raw == "" { return; }

        let args = parse_command(raw);
        if len(args) == 0 { return; }

        let cmd = args[0];

        // ----------------------------------------------------------
        // help – display available commands
        // ----------------------------------------------------------
        if cmd == "help" {
            send("mental_image",
                "=== Nihilo OS Shell ===\n" +
                "  help                           – this message\n" +
                "  status                         – show system info\n" +
                "  timeline list                  – list all timelines\n" +
                "  timeline new                   – create new timeline\n" +
                "  timeline switch <name>         – switch to timeline\n" +
                "  timeline merge <src> <dst>     – merge source into destination\n" +
                "  mosaic write <key> <val> [w]   – store weighted value\n" +
                "  mosaic read <key>              – read most probable value\n" +
                "  mosaic save                    – persist mosaic to disk\n" +
                "  mosaic load                    – load mosaic from disk\n" +
                "  paradox challenge              – request authentication\n" +
                "  paradox verify <code>          – verify challenge response\n" +
                "  collapse <expr> <method>       – collapse probability\n" +
                "  exit                           – shutdown OS",
                20s);
        }

        // ----------------------------------------------------------
        // status – show current timeline, boot time, etc.
        // ----------------------------------------------------------
        else if cmd == "status" {
            let boot = kernel_state.accept("boot_time").read() otherwise "unknown";
            let tl = current_timeline();
            let ready = kernel_state.accept("services_ready").read() otherwise false;
            send("inner_voice",
                "Boot time: " + to_string(boot) + "\n" +
                "Timeline: " + tl + "\n" +
                "Services ready: " + to_string(ready),
                4s);
        }

        // ----------------------------------------------------------
        // timeline commands
        // ----------------------------------------------------------
        else if cmd == "timeline" and len(args) >= 2 {
            let sub = args[1];
            if sub == "list" {
                launch(TimelineManager, "list");
            }
            else if sub == "new" {
                launch(TimelineManager, "create");
            }
            else if sub == "switch" and len(args) >= 3 {
                let name = args[2];
                launch(TimelineManager, "switch|" + name);
            }
            else if sub == "merge" and len(args) >= 4 {
                let src = args[2];
                let dst = args[3];
                launch(TimelineManager, "merge|" + src + "|" + dst);
            }
            else {
                send("tactile", "Usage: timeline {list|new|switch|merge}", 1s);
            }
        }

        // ----------------------------------------------------------
        // mosaic commands – forward to MosaicService
        // ----------------------------------------------------------
        else if cmd == "mosaic" and len(args) >= 2 {
            let sub = args[1];
            if sub == "write" and len(args) >= 4 {
                let key = args[2];
                let val = args[3];
                let weight = if len(args) >= 5 then to_float(args[4]) else 1.0;
                launch(MosaicService, "write|" + key + "|" + val + "|" + to_string(weight));
            }
            else if sub == "read" and len(args) >= 3 {
                let key = args[2];
                launch(MosaicService, "read|" + key);
            }
            else if sub == "save" {
                launch(MosaicService, "save");
            }
            else if sub == "load" {
                launch(MosaicService, "load");
            }
            else {
                send("tactile", "Usage: mosaic {write|read|save|load}", 1s);
            }
        }

        // ----------------------------------------------------------
        // paradox authentication
        // ----------------------------------------------------------
        else if cmd == "paradox" and len(args) >= 2 {
            let sub = args[1];
            if sub == "challenge" {
                launch(ParadoxAuth, "challenge|user");
            }
            else if sub == "verify" and len(args) >= 3 {
                let code = args[2];
                launch(ParadoxAuth, "verify|user|" + code);
            }
            else {
                send("tactile", "Usage: paradox {challenge|verify <code>}", 1s);
            }
        }

        // ----------------------------------------------------------
        // collapse – test probability collapse
        // ----------------------------------------------------------
        else if cmd == "collapse" and len(args) >= 3 {
            let expr = to_float(args[1]);
            let method = args[2];
            let result = collapse(expr, method);
            send("inner_voice", "collapse(" + to_string(expr) + ", " + method + ") = " + to_string(result), 2s);
        }

        // ----------------------------------------------------------
        // exit – save state and shut down
        // ----------------------------------------------------------
        else if cmd == "exit" {
            send("inner_voice", "Saving state and shutting down Nihilo OS...", 1s);
            save_mosaic("state/persistent.json");
            kernel_state.accept("scheduler_running").write(false, 1.0);
            send("mental_image", "Goodbye.", 1s);
            exit();
        }

        // ----------------------------------------------------------
        // unknown command
        // ----------------------------------------------------------
        else {
            send("tactile", "Unknown command. Type 'help'.", 1s);
        }
    }
}
