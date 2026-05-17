// quantum_memory.flux – Quantum memory cells with superposition and collapse.
// Each memory cell can hold multiple values with probability weights.
// Reading collapses the superposition to a concrete state.
// All data is stored in the causal mosaic for persistence across reboots.

causal_mosaic quantum_bank = sparse_temporal_matrix();

// -------------------------------------------------------------------
// Helper: collapse a superposition to a single value using a method
// -------------------------------------------------------------------
function collapse_superposition(entries: list, method: string) -> any {
    if len(entries) == 0 {
        return nil;
    }
    if method == "max_weight" {
        return max(entries, key=lambda e: e.weight).value;
    }
    if method == "random" {
        let total = sum(entries, key=lambda e: e.weight);
        let r = random() * total;
        var acc = 0.0;
        for e in entries {
            acc = acc + e.weight;
            if r <= acc {
                return e.value;
            }
        }
        return entries[0].value;
    }
    if method == "first" {
        return entries[0].value;
    }
    // default: max_weight
    return max(entries, key=lambda e: e.weight).value;
}

// -------------------------------------------------------------------
// Helper: store a superposition entry for a memory cell
// -------------------------------------------------------------------
function write_quantum_cell(address: int, value: any, weight: float) {
    let key = "cell_" + to_string(address);
    let current = quantum_bank.accept(key).read() otherwise [];
    let new_entry = { "value": value, "weight": weight };
    let updated = append(current, new_entry);
    quantum_bank.accept(key).write(updated, 1.0);
}

// -------------------------------------------------------------------
// Helper: read and collapse a quantum cell
// -------------------------------------------------------------------
function read_quantum_cell(address: int, method: string) -> any {
    let key = "cell_" + to_string(address);
    let entries = quantum_bank.accept(key).read() otherwise [];
    return collapse_superposition(entries, method);
}

// -------------------------------------------------------------------
// Quantum Memory Service – provides network‑accessible quantum storage
// -------------------------------------------------------------------
flow QuantumMemoryService {
    execute: {
        while true {
            let cmd = listen("quantum", 200ms, "");
            if cmd == "" { continue; }

            let parts = split(cmd, "|");
            if len(parts) < 2 { continue; }

            let op = parts[0];

            // ---------------------------------------------------------
            // Write: write|address|value|weight
            // ---------------------------------------------------------
            if op == "write" and len(parts) >= 4 {
                let addr = to_int(parts[1]);
                let val = parts[2];
                let w = to_float(parts[3]);
                write_quantum_cell(addr, val, w);
                send("tactile", "quantum write", 100ms);
            }

            // ---------------------------------------------------------
            // Read: read|address|method
            // ---------------------------------------------------------
            else if op == "read" and len(parts) >= 2 {
                let addr = to_int(parts[1]);
                let method = if len(parts) >= 3 then parts[2] else "max_weight";
                let result = read_quantum_cell(addr, method);
                send("inner_voice", "quantum[" ++ to_string(addr) ++ "] = " ++ to_string(result), 1s);
            }

            // ---------------------------------------------------------
            // Entangle: entangle|addr1|addr2 – create correlation (simulated)
            // ---------------------------------------------------------
            else if op == "entangle" and len(parts) >= 3 {
                let addr1 = to_int(parts[1]);
                let addr2 = to_int(parts[2]);
                // Simulate entanglement: force both cells to have identical superpositions
                let key1 = "cell_" + to_string(addr1);
                let key2 = "cell_" + to_string(addr2);
                let sup1 = quantum_bank.accept(key1).read() otherwise [];
                let sup2 = quantum_bank.accept(key2).read() otherwise [];
                if len(sup1) > 0 and len(sup2) > 0 {
                    // For simplicity, merge the two superpositions (union with average weights)
                    let merged = [];
                    for e in sup1 {
                        merged = append(merged, e);
                    }
                    for e in sup2 {
                        merged = append(merged, e);
                    }
                    quantum_bank.accept(key1).write(merged, 1.0);
                    quantum_bank.accept(key2).write(merged, 1.0);
                    send("inner_voice", "Entangled cells " ++ to_string(addr1) ++ " and " ++ to_string(addr2), 1s);
                } else {
                    send("tactile", "Entanglement failed – cells not initialised", 500ms);
                }
            }

            // ---------------------------------------------------------
            // Measure – collapse with forced randomness (quantum measurement)
            // ---------------------------------------------------------
            else if op == "measure" and len(parts) >= 2 {
                let addr = to_int(parts[1]);
                let result = read_quantum_cell(addr, "random");
                send("inner_voice", "Measurement of cell " ++ to_string(addr) ++ ": " ++ to_string(result), 2s);
                // After measurement, the cell collapses to a single definite value
                // (we can optionally discard the superposition)
                let key = "cell_" + to_string(addr);
                quantum_bank.accept(key).write([{ "value": result, "weight": 1.0 }], 1.0);
            }

            // ---------------------------------------------------------
            // Clear – reset a cell to nil
            // ---------------------------------------------------------
            else if op == "clear" and len(parts) >= 2 {
                let addr = to_int(parts[1]);
                let key = "cell_" + to_string(addr);
                quantum_bank.accept(key).write([], 1.0);
                send("tactile", "cell cleared", 200ms);
            }

            else {
                send("tactile", "Unknown quantum command", 300ms);
            }
        }
    }
}

// -------------------------------------------------------------------
// Convenience intention: test quantum memory at boot
// -------------------------------------------------------------------
intention QuantumTest {
    trigger: on_boot()
    priority: 0.8
    condition: kernel_state.accept("services_ready").read() otherwise false
    execute: {
        // Write a superposition of two values with weights 0.7 and 0.3
        write_quantum_cell(42, "alpha", 0.7);
        write_quantum_cell(42, "beta", 0.3);

        // Read with max_weight (deterministic)
        let best = read_quantum_cell(42, "max_weight");
        send("inner_voice", "Most probable at address 42: " ++ to_string(best), 1s);

        // Measure (random collapse)
        let measured = read_quantum_cell(42, "random");
        send("inner_voice", "Measurement result: " ++ to_string(measured), 1s);
    }
}