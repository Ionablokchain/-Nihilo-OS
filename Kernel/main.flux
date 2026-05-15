# main.flux – Pornirea întregului sistem

intention Main {
    trigger: on_boot()
    priority: 1.0
    execute: {
        # Inițializează kernel state
        kernel_state.accept("registered_intentions").write([
            "Bootloader", "Scheduler", "TimelineManager",
            "CausalMosaicService", "ParadoxAuth", "Shell"
        ], 1.0);
        
        # Lansează toate serviciile
        launch(Bootloader);
        
        # Așteaptă până la oprire
        suspend_until_exit();
    }
}