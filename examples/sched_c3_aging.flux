// sched_c3_aging.flux -- C3: aging applied to a low-priority Worker.
//
// Monitor (0.8) always eligible.
// Worker  (0.15) always eligible; the experiment driver sets aging_rate=0.02.
//               After 33 waiting ticks, its effective priority reaches
//               0.15 + 33*0.02 = 0.81, beating Monitor.
// Idle    (0.05) always eligible; catches any tick both others skip.
//
// This is the Flux version of the anti-starvation experiment.

intention Monitor {
    trigger:   on_boot()
    priority:  0.8
    condition: causal_void.exists()
    execute: {
        send("inner_voice", "monitor", 0s);
    }
}

intention Worker {
    trigger:   on_boot()
    priority:  0.15
    condition: causal_void.exists()
    execute: {
        send("mental_image", "worker", 0s);
    }
}

intention Idle {
    trigger:   on_boot()
    priority:  0.05
    condition: causal_void.exists()
    execute: {
        send("tactile", "idle", 0s);
    }
}
