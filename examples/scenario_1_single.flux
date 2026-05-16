// scenario_1_single.flux -- Baseline: one intention, always eligible.
//
// The condition is `true`. The trigger is `on_boot()` which returns
// true always. This measures the minimum possible dispatch latency:
// the condition is true from tick 0, so the scheduler should fire
// at tick 0 and again after every cooldown (experiment sets cooldown=1
// from the outside).
//
// Expected: latency = 0 every time. If anything else is seen, the
// scheduler has a bug.

intention Heartbeat {
    trigger: on_boot()
    priority: 0.5
    condition: causal_void.exists()
    execute: {
        send("tactile", "pulse", 0s);
    }
}
