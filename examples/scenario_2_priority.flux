// scenario_2_priority.flux -- Priority contention.
//
// Two intentions are always eligible. High-priority "Urgent" and
// low-priority "Background". The scheduler should always pick Urgent
// first. Background only runs when Urgent is cooling down (cooldown
// is set from the experiment driver).
//
// Measured quantities:
//   - Urgent's mean latency: should be 0 (dispatched immediately).
//   - Background's mean latency: proportional to Urgent's cooldown.
//   - Fairness: biased toward Urgent (intentionally; Jain < 1).

intention Urgent {
    trigger: on_boot()
    priority: 0.9
    condition: causal_void.exists()
    execute: {
        send("inner_voice", "urgent work", 0s);
    }
}

intention Background {
    trigger: on_boot()
    priority: 0.1
    condition: causal_void.exists()
    execute: {
        send("tactile", "background work", 0s);
    }
}
