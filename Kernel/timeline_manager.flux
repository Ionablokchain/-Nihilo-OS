# timeline_manager.flux – Creează, listează, comută și îmbină timeline-uri

causal_mosaic timeline_registry = sparse_temporal_matrix();

flow TimelineManager {
    execute: {
        while true {
            let cmd = listen("system", 100ms, "");
            
            if cmd == "create" {
                let name = "tl_" + to_string(now());
                let new_tl = create_timeline(name);
                timeline_registry.accept(name).write(new_tl, 1.0);
                send("inner_voice", "Created timeline: " ++ name, 1s);
            }
            else if cmd == "list" {
                let all = timeline_registry.accept("all").read() otherwise [];
                send("mental_image", "Timelines: " ++ to_string(all), 3s);
            }
            else if cmd starts_with "switch " {
                let name = cmd after "switch ";
                set_current_timeline(name);
                send("inner_voice", "Switched to timeline: " ++ name, 1s);
            }
            else if cmd starts_with "merge " {
                let src = cmd after "merge ";
                let dst = current_timeline();
                merge_timelines(src, dst, "keep_target");
                send("inner_voice", "Merged " ++ src ++ " into " ++ dst, 1s);
            }
            
            sleep(50ms);
        }
    }
}