// wake.flux – Nihilo OS bootloader and service launcher
// This intention runs once at startup and brings the whole system to life.

causal_mosaic kernel_state = sparse_temporal_matrix();

// -------------------------------------------------------------------
// Wake – the first intention
// -------------------------------------------------------------------
intention Wake {
    trigger: on_boot()
    priority: 1.0
    condition: causal_void.exists()
    execute: {
        // ---- Initialize kernel state ----
        kernel_state.accept("boot_time").write(now(), 1.0);
        kernel_state.accept("timeline_counter").write(1, 1.0);
        kernel_state.accept("services_ready").write(false, 1.0);
        kernel_state.accept("scheduler_running").write(true, 1.0);

        // ---- Load persistent mosaic (if any) ----
        load_mosaic("state/persistent.json");

        // ---- Announce boot ----
        send("inner_voice", "Nihilo OS waking up...", 2s);
        send("mental_image", "╔════════════════════════════════════════╗\n"
                           "║  Nihilo OS – The Operating System       ║\n"
                           "║  from Nothing                           ║\n"
                           "╚════════════════════════════════════════╝", 5s);

        // ---- Launch core services (each runs as a background flow) ----
        launch(Scheduler);           // priority‑based intention scheduler
        launch(TimelineManager);     // timeline creation, switching, merging
        launch(CausalMosaicService); // persistent key‑value store
        launch(ParadoxAuth);         // authentication via temporal paradoxes
        launch(Shell);               // user REPL

        // ---- Allow services to initialise ----
        sleep(500ms);
        kernel_state.accept("services_ready").write(true, 1.0);

        // ---- Final ready signal ----
        send("inner_voice", "All services launched. Type 'help' for commands.", 3s);
        send("tactile", "two short pulses", 0.5s);
    }
}