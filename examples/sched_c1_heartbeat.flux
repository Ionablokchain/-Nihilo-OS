// sched_c1_heartbeat.flux -- C1: single always-eligible intention.
//
// The scheduler evaluates `causal_void.exists()` via the real TVM at
// every tick. When it returns true (which it always does), this
// intention is dispatched. This is the Flux equivalent of Scenario A1.

intention Heartbeat {
    trigger:   on_boot()
    priority:  0.5
    condition: causal_void.exists()
    execute: {
        send("tactile", "pulse", 0s);
    }
}
