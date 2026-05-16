// causal_mosaic.flux -- Persistence without files.
//
// CONCEPT
// A traditional OS stores user data in files: named byte sequences on
// disk. Nihilo's mosaic is the same idea taken in another direction:
// a sparse map from keys to *weighted* values. Multiple writes to the
// same key do not overwrite; they add weighted branches. A read
// collapses to the most probable branch (or to whatever method the
// program picks).
//
// In a real OS this would need a storage layer; here it lives in
// process memory for the duration of the program.

causal_mosaic notes = sparse_temporal_matrix();

intention WriteNotes {
    trigger: on_boot()
    priority: 0.9
    execute: {
        notes.accept("today").write("buy groceries", 0.3);
        notes.accept("today").write("call mom",      0.7);
        notes.accept("today").write("walk the dog",  0.1);
        send("inner_voice", "three notes recorded with different priorities", 1s);
    }
}

intention RecallNote {
    trigger: on_boot()
    priority: 0.5
    execute: {
        let primary = notes.accept("today").read();
        send("mental_image", "most likely note: " ++ to_string(primary), 2s);
    }
}
