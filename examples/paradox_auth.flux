// paradox_auth.flux -- Authentication by mutual recall of a generated token.
//
// CONCEPT
// In a procedural OS, "password" is a comparison of two strings. In
// Nihilo's vocabulary, a "paradox" is a generated token that the user
// must echo back in the same causal window. The token is generated
// deterministically by the runtime; the test of identity is whether
// the user supplies the same value back.
//
// CONCEPT vs IMPLEMENTATION
// generate_paradox() here is a deterministic counter-derived string,
// not a real cryptographic challenge. This file demonstrates the SHAPE
// of the protocol -- generate, challenge, verify -- without claiming
// it has any security properties.

causal_mosaic auth_log = sparse_temporal_matrix();

function authenticate() -> bool {
    let token = generate_paradox();
    auth_log.accept("issued").write(token, 1.0);
    send("inner_voice", "challenge: " ++ to_string(token), 1s);
    let reply = listen(user, 10s, token);
    return reply == token;
}

intention Authenticate {
    trigger: on_command("login")
    priority: 0.9
    execute: {
        if authenticate() {
            send("mental_image", "access granted", 2s);
            auth_log.accept("result").write("granted", 1.0);
        } else {
            send("tactile", "access denied", 1s);
            auth_log.accept("result").write("denied", 1.0);
        }
    }
}
