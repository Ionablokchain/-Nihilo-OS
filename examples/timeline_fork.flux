// timeline_fork.flux -- Forking and merging timelines.
//
// CONCEPT
// In a traditional OS, fork() creates a copy of a process. In Nihilo's
// model, create_timeline() creates a *causal branch*: a new timeline
// in which subsequent intentions can run independently. Merging brings
// the branch's writes back into the main timeline.
//
// In this demo the runtime models timelines as a set of named labels
// with a single currently-active one. The "merge" is symbolic: the
// label is forgotten. Real causal-merge semantics (resolving conflicts
// between concurrent writes) are out of scope.

intention Fork {
    trigger: on_boot()
    priority: 0.7
    execute: {
        let origin = current_timeline();
        send("inner_voice", "starting on: " ++ origin, 1s);

        let branch = create_timeline();
        set_current_timeline(branch);
        send("inner_voice", "switched to: " ++ current_timeline(), 1s);

        // ... work would happen here on the branch ...
        sleep(2s);

        merge_timelines(branch, origin);
        set_current_timeline(origin);
        send("inner_voice", "merged back to: " ++ current_timeline(), 1s);
    }
}
