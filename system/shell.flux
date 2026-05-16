# shell.flux – Prima interfață neuronală

causal_mosaic user_prefs = sparse_temporal_matrix();

intention Shell {
    trigger: on_user_intention()
    priority: 0.8
    execute: {
        let cmd = listen("user", 5s, "help");
        
        if cmd == "help" {
            send("mental_image", 
                "Commands:\n"
                "  timeline list\n"
                "  timeline new\n"
                "  timeline switch <name>\n"
                "  mosaic write <key> <value> [weight]\n"
                "  mosaic read <key>\n"
                "  paradox challenge\n"
                "  collapse <expr> <method>\n"
                "  exit", 10s);
        }
        else if cmd == "timeline list" {
            launch(TimelineManager, "list");
        }
        else if cmd starts_with "timeline new" {
            launch(TimelineManager, "create");
        }
        else if cmd starts_with "timeline switch " {
            launch(TimelineManager, cmd);
        }
        else if cmd starts_with "mosaic write " {
            let rest = cmd after "mosaic write ";
            launch(CausalMosaicService, rest);
        }
        else if cmd starts_with "mosaic read " {
            let key = cmd after "mosaic read ";
            let val = system_mosaic.accept(key).read() otherwise "<not found>";
            send("inner_voice", key ++ " = " ++ to_string(val), 2s);
        }
        else if cmd == "paradox challenge" {
            launch(ParadoxAuth, "user");
        }
        else if cmd == "exit" {
            send("inner_voice", "Shutting down Nihilo OS. Goodbye.", 2s);
            retire_current_intention();
        }
        else {
            send("tactile", "Unknown command. Type 'help' for list.", 1s);
        }
    }
}