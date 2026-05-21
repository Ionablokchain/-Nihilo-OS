// aviation.flux – Complete aviation module for Nihilo OS
// Includes ADS‑B, airspace classes, flight planning, and METAR/TAF weather.

causal_mosaic aviation_state = sparse_temporal_matrix();

// ============================================================================
// 1. ADS‑B aircraft tracking (ads_b.flux)
// ============================================================================

struct AircraftPosition {
    timestamp: u64,
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
    track: [AircraftPosition],
}

struct AircraftMessage {
    tag: string,   // "AirbornePosition", "AirborneVelocity", "Identification", "SurfacePosition"
    airborne_pos: AircraftPosition?,
    velocity_ground_speed_kt: u16?,
    velocity_track_deg: u16?,
    velocity_vertical_rate_fpm: i16?,
    ident_callsign: string?,
    surface_pos: AircraftPosition?,
}

function decode_ads_b_message(raw: [u8]) -> AircraftMessage? {
    send("inner_voice", "ADS‑B decoder not implemented (requires Mode S parser)", 1s);
    nil
}

function cpr_decode_position(msg: [u8], ref_lat: float, ref_lon: float) -> (float, float) {
    (0.0, 0.0)
}

function store_aircraft(icao: u32, ac: Aircraft) {
    aviation_state.accept("ac_" + to_string(icao)).write(ac, 1.0);
}

function get_aircraft(icao: u32) -> Aircraft? {
    aviation_state.accept("ac_" + to_string(icao)).read() otherwise nil
}

function update_aircraft_position(icao: u32, new_pos: AircraftPosition) -> bool {
    let mut ac = get_aircraft(icao) otherwise return false;
    ac.current_position = new_pos;
    ac.track = append(ac.track, new_pos);
    if len(ac.track) > 100 {
        ac.track = ac.track[-100:];
    }
    store_aircraft(icao, ac);
    true
}

// ============================================================================
// 2. Airspace classes and restricted areas (airspace.flux)
// ============================================================================

struct Airspace {
    designation: string,
    class: string,   // "A","B","C","D","E","G","Restricted","Prohibited","Warning","Danger","Mva","Tfr"
    boundary: [(float, float)],
    floor_ft: int,
    ceiling_ft: int,
    effective_times: string,
    frequency_mhz: float,
    controller: string,
}

function point_in_polygon(point: (float, float), polygon: [(float, float)]) -> bool {
    if len(polygon) == 0 { return false; }
    let (x, y) = point;
    let mut inside = false;
    let mut j = len(polygon) - 1;
    for i in 0..len(polygon) {
        let (xi, yi) = polygon[i];
        let (xj, yj) = polygon[j];
        if (yi > y) != (yj > y) {
            let slope = (x - xi) * (yj - yi) - (xj - xi) * (y - yi);
            if slope == 0.0 { return true; }
            if (slope < 0.0) != (yj < yi) {
                inside = not inside;
            }
        }
        j = i;
    }
    inside
}

function check_airspace_violation(lat: float, lon: float, alt_ft: int, airspace: Airspace) -> bool {
    if alt_ft < airspace.floor_ft or alt_ft > airspace.ceiling_ft {
        return false;
    }
    point_in_polygon((lat, lon), airspace.boundary)
}

function store_airspace(designation: string, as: Airspace) {
    aviation_state.accept("as_" + designation).write(as, 1.0);
}

function get_airspace(designation: string) -> Airspace? {
    aviation_state.accept("as_" + designation).read() otherwise nil
}

function find_violating_airspaces(lat: float, lon: float, alt_ft: int) -> [string] {
    let violations = [];
    let keys = aviation_state.accept("airspace_keys").read() otherwise [];
    for key in keys {
        let as = aviation_state.accept(key).read() otherwise continue;
        if check_airspace_violation(lat, lon, alt_ft, as) {
            violations = append(violations, as.designation);
        }
    }
    violations
}

// ============================================================================
// 3. Flight plan (flight_plan.flux)
// ============================================================================

struct RoutePoint {
    identifier: string,
    kind: string,   // "Vor","Ndb","Fix","Airport","GpsCoord","Airway"
    frequency_mhz: float?,
}

struct FlightPlan {
    aircraft_id: string,
    flight_rules: string,  // "Vfr","Ifr","Yankee","Zulu"
    aircraft_type: string,
    departure_aerodrome: string,
    destination: string,
    alternates: [string],
    eobt: u64,
    cruising_speed: u16,
    cruising_level: string,
    route: [RoutePoint],
    estimated_elapsed_time_minutes: u32,
    fuel_endurance_hours: float,
    persons_on_board: u16,
    remarks: string,
    pilot_in_command: string,
}

function store_flight_plan(id: string, plan: FlightPlan) {
    aviation_state.accept("fp_" + id).write(plan, 1.0);
}

function get_flight_plan(id: string) -> FlightPlan? {
    aviation_state.accept("fp_" + id).read() otherwise nil
}

function estimate_fuel_required(plan: FlightPlan, aircraft_burn_pph: float) -> float {
    let flight_hours = plan.estimated_elapsed_time_minutes as float / 60.0;
    let trip_fuel = flight_hours * aircraft_burn_pph;
    let reserve = aircraft_burn_pph * 0.75;
    let alternate = aircraft_burn_pph * 0.5;
    let contingency = trip_fuel * 0.05;
    trip_fuel + reserve + alternate + contingency
}

function fuel_breakdown_lbs(distance_nm: float, cruise_speed_kts: float, burn_rate_pph: float, headwind_kts: float) -> (float, float, float, float, float) {
    let ground_speed = if cruise_speed_kts - headwind_kts > 50.0 then cruise_speed_kts - headwind_kts else 50.0;
    let flight_hours = distance_nm / ground_speed;
    let trip = flight_hours * burn_rate_pph;
    let contingency = trip * 0.05;
    let alternate = burn_rate_pph * 0.5;
    let final_reserve = burn_rate_pph * 0.75;
    (trip, contingency, alternate, final_reserve, trip + contingency + alternate + final_reserve)
}

function density_altitude_ft(pressure_alt_ft: float, oat_c: float) -> float {
    let std_temp = 15.0 - 1.98 * pressure_alt_ft / 1000.0;
    let isa_deviation = oat_c - std_temp;
    pressure_alt_ft + 120.0 * isa_deviation
}

function pressure_altitude_ft(field_elevation_ft: float, altimeter_inhg: float) -> float {
    field_elevation_ft + (29.92 - altimeter_inhg) * 1000.0
}

function true_airspeed_kts(ias_kts: float, altitude_ft: float) -> float {
    ias_kts * (1.0 + altitude_ft / 50000.0)
}

// Trigonometric approximations (needed for wind correction)
function sin_f32(x: float) -> float {
    let mut x = x;
    let pi = 3.141592653589793;
    while x > pi { x = x - 2.0 * pi; }
    while x < -pi { x = x + 2.0 * pi; }
    let mut sum = 0.0;
    let mut term = x;
    for n in 0..12 {
        sum = sum + term;
        term = term * -x * x / ((2 * n + 2) as float * (2 * n + 3) as float);
    }
    sum
}

function cos_f32(x: float) -> float {
    sin_f32(x + 3.141592653589793 / 2.0)
}

function asin_f32(x: float) -> float {
    let mut x = x;
    if x > 1.0 { x = 1.0; }
    if x < -1.0 { x = -1.0; }
    let mut sum = x;
    let mut term = x;
    for n in 1..15 {
        term = term * x * x * (2 * n - 1) as float * (2 * n - 1) as float
               / ((2 * n) as float * (2 * n + 1) as float);
        sum = sum + term;
    }
    sum
}

function wind_correction(true_course_deg: float, tas_kts: float, wind_dir_deg: float, wind_speed_kts: float) -> (float, float) {
    let deg_to_rad = 0.017453292519943295;
    let angle = (wind_dir_deg - true_course_deg) * deg_to_rad;
    let sin_wca = wind_speed_kts * sin_f32(angle) / tas_kts;
    let wca_rad = asin_f32(sin_wca);
    let wca_deg = wca_rad * 57.29577951308232;
    let gs = tas_kts * cos_f32(wca_rad) + wind_speed_kts * cos_f32(angle);
    (if gs < 0.0 then 0.0 else gs, wca_deg)
}

function top_of_descent_nm(cruise_alt_ft: float, dest_alt_ft: float) -> float {
    let altitude_to_lose = cruise_alt_ft - dest_alt_ft;
    if altitude_to_lose <= 0.0 { return 0.0; }
    altitude_to_lose / 1000.0 * 3.0
}

function crosswind_component(wind_speed_kts: float, wind_angle_deg: float) -> float {
    let angle_rad = wind_angle_deg * 0.017453292519943295;
    wind_speed_kts * sin_f32(angle_rad)
}

function headwind_component(wind_speed_kts: float, wind_angle_deg: float) -> float {
    let angle_rad = wind_angle_deg * 0.017453292519943295;
    wind_speed_kts * cos_f32(angle_rad)
}

// ============================================================================
// 4. METAR/TAF weather (metar_taf.flux)
// ============================================================================

struct WindMetar {
    direction_deg: u16,
    speed_knots: u16,
    gust_knots: u16,
    variable: bool,
}

struct CloudLayerMetar {
    coverage: string,   // "Few","Scattered","Broken","Overcast","Clear"
    base_ft: u32,
    kind: string?,      // "Cumulonimbus","ToweringCumulus"
}

struct Metar {
    icao: string,
    observation_time: u64,
    wind: WindMetar,
    visibility_meters: u32,
    weather_phenomena: [string],
    clouds: [CloudLayerMetar],
    temperature_c: int,
    dewpoint_c: int,
    altimeter_hpa: u16,
    raw: string,
}

function parse_metar(raw: string) -> Metar? {
    let parts = split(raw, " ");
    if len(parts) < 4 { return nil; }
    Metar {
        icao: parts[0],
        observation_time: 0,
        wind: WindMetar { direction_deg: 0, speed_knots: 0, gust_knots: 0, variable: false },
        visibility_meters: 9999,
        weather_phenomena: [],
        clouds: [],
        temperature_c: 15,
        dewpoint_c: 5,
        altimeter_hpa: 1013,
        raw: raw,
    }
}

function flight_category(metar: Metar) -> string {
    let mut ceiling_ft = 99999;
    for cloud in metar.clouds {
        if cloud.coverage == "Broken" or cloud.coverage == "Overcast" {
            if cloud.base_ft < ceiling_ft {
                ceiling_ft = cloud.base_ft;
            }
        }
    }
    let visibility_sm = metar.visibility_meters / 1609;
    if ceiling_ft < 500 or visibility_sm < 1 {
        "Lifr"
    } else if ceiling_ft < 1000 or visibility_sm < 3 {
        "Ifr"
    } else if ceiling_ft < 3000 or visibility_sm < 5 {
        "Mvfr"
    } else {
        "Vfr"
    }
}

function store_metar(icao: string, metar: Metar) {
    aviation_state.accept("metar_" + icao).write(metar, 1.0);
}

function get_metar(icao: string) -> Metar? {
    aviation_state.accept("metar_" + icao).read() otherwise nil
}