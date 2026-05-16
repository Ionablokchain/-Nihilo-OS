// boot.flux -- The first intention. Initializes shared state.
//
// In a procedural OS this would be init/systemd. In Nihilo's model
// it is just an intention with high priority that triggers on_boot.
// The mosaic plays the role of shared kernel state; the timeline
// concept replaces the idea of a single global clock.

causal_mosaic kernel_state = sparse_temporal_matrix();

intention Boot {
    trigger: on_boot()
    priority: 1.0
    condition: causal_void.exists()
    execute: {
        kernel_state.accept("boot_time").write(now(), 1.0);
        kernel_state.accept("timeline").write(current_timeline(), 1.0);
        send("inner_voice", "Nihilo OS booting on timeline " ++ current_timeline(), 2s);
        send("mental_image", "system ready", 1s);
    }
}
