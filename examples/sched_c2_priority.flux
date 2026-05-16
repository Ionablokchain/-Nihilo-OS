// sched_c2_priority.flux -- C2: two intentions, priority 0.9 vs 0.2.
//
// Both conditions use causal_void.exists() so they are always eligible.
// The scheduler re-evaluates each condition via TVM at every tick and
// dispatches the higher-priority one first. Monitor writes to the
// shared mosaic to count how many times each intention ran.

causal_mosaic counters = sparse_temporal_matrix();

intention HighPriority {
    trigger:   on_boot()
    priority:  0.9
    condition: causal_void.exists()
    execute: {
        send("inner_voice", "high", 0s);
    }
}

intention LowPriority {
    trigger:   on_boot()
    priority:  0.2
    condition: causal_void.exists()
    execute: {
        send("tactile", "low", 0s);
    }
}
