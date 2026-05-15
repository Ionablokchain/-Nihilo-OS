# bootstrap.flux – Primele intenții executate la boot

causal_mosaic kernel_state = sparse_temporal_matrix();

intention Bootloader {
    trigger: on_boot()
    priority: 1.0
    condition: causal_void.exists()
    execute: {
        send("inner_voice", "Booting Nihilo OS...", 2s);
        
        # Inițializează kernel state
        kernel_state.accept("boot_time").write(now(), 1.0);
        kernel_state.accept("timeline_count").write(1, 1.0);
        
        # Lansează serviciile de bază
        launch(Scheduler);
        launch(TimelineManager);
        launch(CausalMosaicService);
        
        send("mental_image", "Nihilo OS ready. Type 'help' for commands.", 5s);
    }
}