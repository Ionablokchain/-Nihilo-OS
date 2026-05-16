// scenario_3_late_condition.flux -- Late eligibility.
//
// Three intentions:
//   - "Fast": always eligible (priority 0.8). Fires every tick.
//   - "Slow":  condition becomes true after tick 200 (simulated
//              by the experiment driver which patches the condition).
//              Priority 0.7.
//   - "Idle":  always eligible, very low priority (0.05). Only runs
//              when both Fast and Slow are cooling down.
//
// Measured quantities:
//   - Slow's eligibility-to-dispatch latency: should be 0 once
//     eligible (because its priority 0.7 > Idle's 0.05, and Fast
//     is cooling down on the same tick Slow becomes eligible).
//   - Idle's starvation: does it ever run?

intention Fast {
    trigger: on_boot()
    priority: 0.8
    condition: causal_void.exists()
    execute: {
        send("tactile", "fast tick", 0s);
    }
}

intention Slow {
    trigger: on_boot()
    priority: 0.7
    condition: causal_void.exists()
    execute: {
        send("inner_voice", "slow triggered", 0s);
    }
}

intention Idle {
    trigger: on_boot()
    priority: 0.05
    condition: causal_void.exists()
    execute: {
        send("mental_image", "idle filler", 0s);
    }
}
