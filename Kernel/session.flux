// session.flux -- The user "shell" modeled as a single intention.
//
// Traditional OS shells are read-eval-print loops: blocking input,
// dispatch on string, execute. Nihilo's model collapses that loop
// into a single intention with a condition. The condition is what
// distinguishes a "ready to listen" state from any other. In a real
// scheduler this intention would be re-fired whenever the condition
// becomes true; the demo runs it once.

causal_mosaic session_state = sparse_temporal_matrix();

intention Session {
    trigger: on_user_intention()
    priority: 0.9
    execute: {
        let cmd = listen(user, 5s, "help");
        session_state.accept("last_command").write(cmd, 1.0);

        if cmd == "help" {
            send("mental_image",
                 "commands: help | status | decide | exit",
                 4s);
        } else {
            if cmd == "status" {
                let last = session_state.accept("last_command").read();
                send("inner_voice", "last command was: " ++ to_string(last), 2s);
            } else {
                if cmd == "exit" {
                    send("inner_voice", "session retiring", 1s);
                } else {
                    send("tactile", "unknown command", 500ms);
                }
            }
        }
    }
}
