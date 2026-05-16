// paradox_engine.flux – Authentication service using temporal paradoxes.
// Generates and verifies paradox challenges for user authentication.
//
// Commands (sent via listen("paradox")):
//   challenge|user   – generate a new paradox challenge for the user
//   verify|user|code – verify a user's response to a challenge
//   status|user      – check if a user is authenticated

causal_mosaic paradox_db = sparse_temporal_matrix();
causal_mosaic kernel_state = sparse_temporal_matrix();

// -------------------------------------------------------------------
// Helper: generate a new paradox challenge for a user
// -------------------------------------------------------------------
function generate_challenge(user: string) -> string {
    // Generate a prime‑interval paradox of length 3 using the current time as seed
    let seed = now() as int;
    let length = 3;
    let p = generate_paradox("prime_interval", seed, length, 0);
    // Store the challenge in the database
    paradox_db.accept(user).write(p, 1.0);
    return to_string(p);
}

// -------------------------------------------------------------------
// Helper: verify a user's response against the stored challenge
// -------------------------------------------------------------------
function verify_challenge(user: string, response: string) -> bool {
    let stored = paradox_db.accept(user).read() otherwise "";
    return stored == response;
}

// -------------------------------------------------------------------
// Helper: check if a user is already authenticated
// -------------------------------------------------------------------
function is_authenticated(user: string) -> bool {
    let auth_flag = kernel_state.accept("auth_" ++ user).read() otherwise false;
    return auth_flag;
}

// -------------------------------------------------------------------
// ParadoxAuth service – listens for authentication commands
// -------------------------------------------------------------------
flow ParadoxAuth {
    execute: {
        while true {
            let cmd = listen("paradox", 1s, "");
            if cmd == "" { continue; }

            let parts = split(cmd, "|");
            if len(parts) == 0 { continue; }

            let command = parts[0];

            // -----------------------------------------------------------------
            // Challenge generation: challenge|user
            // -----------------------------------------------------------------
            if command == "challenge" and len(parts) >= 2 {
                let user = parts[1];
                let challenge = generate_challenge(user);
                send("inner_voice", "Paradox challenge for " ++ user ++ ": " ++ challenge, 4s);
                send("tactile", "challenge sent", 500ms);
            }

            // -----------------------------------------------------------------
            // Verification: verify|user|response
            // -----------------------------------------------------------------
            else if command == "verify" and len(parts) >= 3 {
                let user = parts[1];
                let response = parts[2];

                if verify_challenge(user, response) {
                    send("mental_image", "Access granted for " ++ user ++ ".", 2s);
                    kernel_state.accept("auth_" ++ user).write(true, 1.0);
                    // Optionally remove the used challenge
                    paradox_db.accept(user).delete();
                } else {
                    send("tactile", "Access denied. Timeline reset for " ++ user ++ ".", 1s);
                    reset_timeline(user);
                    // Clear any stored challenge for this user
                    paradox_db.accept(user).delete();
                }
            }

            // -----------------------------------------------------------------
            // Status check: status|user
            // -----------------------------------------------------------------
            else if command == "status" and len(parts) >= 2 {
                let user = parts[1];
                let auth_status = is_authenticated(user);
                if auth_status {
                    send("inner_voice", user ++ " is authenticated.", 1s);
                } else {
                    send("inner_voice", user ++ " is NOT authenticated.", 1s);
                }
            }

            // -----------------------------------------------------------------
            // Unknown command
            // -----------------------------------------------------------------
            else {
                send("tactile", "Bad paradox command. Use: challenge|user, verify|user|code, status|user", 2s);
            }
        }
    }
}
