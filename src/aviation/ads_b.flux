// adsb.flux – ADS‑B aircraft tracking (stub implementation)

causal_mosaic adsb_state = sparse_temporal_matrix();

// ------------------------------------------------------------------
// Data structures
// ------------------------------------------------------------------
struct AircraftPosition {
    timestamp: u64,        // Unix seconds
    latitude: float,
    longitude: float,
    altitude_ft: int,
    ground_speed_kt: u16,
    track_deg: u16,
    vertical_rate_fpm: i16,
    squawk: u16,
    emergency: bool,
    on_ground: bool,
}

struct Aircraft {
    icao_address: u32,
    callsign: string,
    registration: string,
    aircraft_type: string,
    current_position: AircraftPosition,
    track: [AircraftPosition],   // history of positions
}

// ------------------------------------------------------------------
// ADSB message types (represented as tagged unions using structs)
// ------------------------------------------------------------------
struct AirbornePosition {
    position: AircraftPosition,
}

struct AirborneVelocity {
    ground_speed_kt: u16,
    track_deg: u16,
    vertical_rate_fpm: i16,
}

struct Identification {
    callsign: string,
}

struct SurfacePosition {
    position: AircraftPosition,
}

// The AircraftMessage enum is represented by a choice of these structs.
// In Flux we can simulate this using a single struct with an explicit tag.
struct AircraftMessage {
    tag: string,   // "AirbornePosition", "AirborneVelocity", "Identification", "SurfacePosition"
    // payload as optional fields (only one will be non‑nil)
    airborne_pos: AircraftPosition?,
    velocity: AirborneVelocity?,
    ident: Identification?,
    surface_pos: AircraftPosition?,
}

// ------------------------------------------------------------------
// Stub decoder functions
// ------------------------------------------------------------------
function decode_ads_b_message(raw: [u8]) -> AircraftMessage? {
    // Stub: always returns nil (error) – full implementation requires Mode S parser
    // In real code, you would implement the parsing here.
    // For now, return a dummy error by returning nil.
    // Optionally, you could write a diagnostic message.
    send("inner_voice", "ADS-B decoder not implemented (requires Mode S parser)", 1s);
    nil
}

function cpr_decode_position(msg: [u8], ref_lat: float, ref_lon: float) -> (float, float) {
    // Stub: returns (0.0, 0.0)
    // In real implementation, this would decode Compact Position Reporting.
    (0.0, 0.0)
}

// ------------------------------------------------------------------
// Helper: store aircraft in mosaic
// ------------------------------------------------------------------
function store_aircraft(aircraft: Aircraft) {
    let key = "ac_" + to_string(aircraft.icao_address);
    adsb_state.accept(key).write(aircraft, 1.0);
}

function get_aircraft(icao: u32) -> Aircraft? {
    let key = "ac_" + to_string(icao);
    adsb_state.accept(key).read() otherwise nil
}

function update_aircraft_position(icao: u32, new_pos: AircraftPosition) -> bool {
    let mut ac = get_aircraft(icao) otherwise return false;
    // Update current position
    ac.current_position = new_pos;
    // Append to track (keep last 100 positions)
    ac.track = append(ac.track, new_pos);
    if len(ac.track) > 100 {
        ac.track = ac.track[-100:];
    }
    store_aircraft(ac);
    true
}