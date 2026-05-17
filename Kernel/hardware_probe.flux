// hardware_probe.flux – Hardware detection and dynamic driver synthesis.
// Part of the fractal kernel: the OS writes its own drivers at boot.
//
// This file assumes the TVM provides a built‑in object `hardware` with:
//   hardware.devices() -> list of device names
//   hardware.capabilities(device) -> map of capability strings
//   hardware.claim(device, driver) -> bool
//   hardware.read(device, register) -> value
//   hardware.write(device, register, value)
//
// In a real system, these would interface with actual hardware;
// in the TVM they are simulated (e.g., return a fixed device list).

causal_mosaic kernel_state = sparse_temporal_matrix();
causal_mosaic driver_registry = sparse_temporal_matrix();

// -------------------------------------------------------------------
// Helper: generate a driver intention for a specific device
// -------------------------------------------------------------------
function synthesize_driver(device: string, caps: map) -> string {
    let driver_name = "driver_" ++ device;
    // Build the driver body as a string (in a real system, this would be
    // injected into the runtime; here we just register a placeholder intention).
    let driver_code = "
intention " ++ driver_name ++ " {
    trigger: on_hardware_interrupt(" ++ device ++ ")
    priority: 0.7
    execute: {
        let data = hardware.read(" ++ device ++ ", 0);
        send(\"inner_voice\", \"Driver for " ++ device ++ " processed data: \" ++ to_string(data), 1s);
    }
}";
    // In the TVM, we would compile and register this intention.
    // For now, we register it in the driver_registry mosaic.
    driver_registry.accept(driver_name).write({
        "device": device,
        "capabilities": caps,
        "status": "active"
    }, 1.0);
    return driver_name;
}

// -------------------------------------------------------------------
// Main probe intention – runs at boot to detect and install drivers
// -------------------------------------------------------------------
intention HardwareProbe {
    trigger: on_boot()
    priority: 0.9
    condition: causal_void.exists()
    execute: {
        send("inner_voice", "Probing hardware...", 1s);

        // Get list of available devices from the hardware abstraction layer
        let devices = hardware.devices();
        if len(devices) == 0 {
            send("tactile", "No hardware devices detected.", 1s);
            return;
        }

        var installed = 0;
        for dev in devices {
            let caps = hardware.capabilities(dev);
            send("inner_voice", "Found device: " ++ dev ++ " with capabilities: " ++ to_string(caps), 2s);

            // Attempt to claim the device (prevents other drivers from using it)
            let claimed = hardware.claim(dev, "flux_driver");
            if claimed {
                let driver_name = synthesize_driver(dev, caps);
                send("inner_voice", "Installed driver: " ++ driver_name, 1s);
                installed = installed + 1;
            } else {
                send("tactile", "Could not claim device: " ++ dev, 500ms);
            }
        }

        // Store the list of installed drivers in kernel state
        kernel_state.accept("installed_drivers").write(installed, 1.0);
        kernel_state.accept("driver_ready").write(true, 1.0);

        send("inner_voice", "Hardware probe complete. " ++ to_string(installed) ++ " drivers installed.", 2s);
        send("tactile", "three short pulses", 500ms);
    }
}

// -------------------------------------------------------------------
// Optional: periodic hardware refresh (for hotplug support)
// -------------------------------------------------------------------
flow HardwareMonitor {
    execute: {
        while true {
            // Check for new devices every 10 seconds
            sleep(10s);
            let new_devices = hardware.devices();
            let known = kernel_state.accept("known_devices").read() otherwise [];
            for dev in new_devices {
                if not (dev in known) {
                    // New device detected – trigger a driver synthesis
                    send("inner_voice", "New device detected: " ++ dev, 1s);
                    launch(HardwareProbe);
                }
            }
            kernel_state.accept("known_devices").write(new_devices, 1.0);
        }
    }
}