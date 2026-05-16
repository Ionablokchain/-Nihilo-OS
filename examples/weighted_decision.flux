// weighted_decision.flux -- Decisions modeled as collapse of distributions.
//
// CONCEPT
// In a procedural OS, a scheduler picks the next task by an exact
// algorithm (round-robin, priority queue, CFS). In Nihilo's vocabulary,
// a scheduler is a distribution over candidate intentions, and a
// "schedule" is a collapse of that distribution by some method:
// max_weight is deterministic, weighted_random is stochastic, mean
// is meaningful only for numeric distributions.
//
// This file demonstrates the move from belief (a distribution) to
// commitment (a single value).

intention Decide {
    trigger: on_boot()
    priority: 0.8
    execute: {
        let candidates = dist {
            "background_cleanup": 0.5,
            "user_request":       0.3,
            "network_poll":       0.2
        };

        // Deterministic schedule: pick the most-likely intention.
        let chosen = collapse(candidates, max_weight);
        send("mental_image", "scheduled (max): " ++ chosen, 1s);

        // Stochastic schedule: sample proportional to weights.
        let sampled = collapse(candidates, weighted_random);
        send("inner_voice", "scheduled (sampled): " ++ sampled, 1s);

        send("inner_voice",
             "P(background) = " ++ to_string(weight_of(candidates, "background_cleanup")),
             500ms);
    }
}
