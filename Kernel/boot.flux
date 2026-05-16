// boot.flux – First intention executed at system start.
// Initializes shared kernel state and launches essential services.

causal_mosaic kernel_state = sparse_temporal_matrix();

// -------------------------------------------------------------------
// Boot intention – runs once when the OS starts
// -------------------------------------------------------------------

intention Boot {
    trigger: on_boot()
    priority: 1.0
    condition: causal_void.exists()
    execute: {
        // Record boot timestamp and initial timeline
        kernel_state.accept("boot_time").write(now(), 1.0);
        kernel_state.accept("timeline").write(current_timeline(), 1.0);
        kernel_state.accept("timeline_counter").write(1, 1.0);
        kernel_state.accept("services_ready").write(false, 1.0);

        // Announce boot
        send("inner_voice", "Nihilo OS booting on timeline " ++ current_timeline(), 2s);

        // Launch core system services (each runs as a background flow)
        launch(Scheduler);           // priority‑based intention scheduler
        launch(TimelineManager);     // timeline creation, switching, merging
        launch(CausalMosaicService); // persistent key‑value store
        launch(ParadoxEngine);       // authentication via temporal puzzles
        launch(Shell);               // user REPL

        // Allow services to initialize
        sleep(500ms);
        kernel_state.accept("services_ready").write(true, 1.0);

        // Final ready signal
        send("mental_image", "System ready. Type 'help' for commands.", 3s);
    }
}
