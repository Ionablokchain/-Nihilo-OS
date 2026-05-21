// flight_plan.flux – ICAO flight planning calculations

causal_mosaic flight_state = sparse_temporal_matrix();

// ------------------------------------------------------------------
// Data structures
// ------------------------------------------------------------------
// Flight rules as strings: "Vfr", "Ifr", "Yankee", "Zulu"
// Waypoint kinds: "Vor", "Ndb", "Fix", "Airport", "GpsCoord", "Airway"

struct RoutePoint {
    identifier: string,
    kind: string,        // WaypointKind as string
    frequency_mhz: float?,   // optional
}

struct FlightPlan {
    aircraft_id: string,
    flight_rules: string,
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

// ------------------------------------------------------------------
// Helper: store and retrieve flight plans
// ------------------------------------------------------------------
function store_flight_plan(id: string, plan: FlightPlan) {
    flight_state.accept("fp_" ++ id).write(plan, 1.0);
}

function get_flight_plan(id: string) -> FlightPlan? {
    flight_state.accept("fp_" ++ id).read() otherwise nil
}

// ------------------------------------------------------------------
// Fuel estimation functions
// ------------------------------------------------------------------
function estimate_fuel_required(plan: FlightPlan, aircraft_burn_pph: float) -> float {
    let flight_hours = plan.estimated_elapsed_time_minutes as float / 60.0;
    let trip_fuel = flight_hours * aircraft_burn_pph;
    let reserve = aircraft_burn_pph * 0.75;     // 45‑min final reserve (FAR 91.167)
    let alternate = aircraft_burn_pph * 0.5;    // alternate fuel
    let contingency = trip_fuel * 0.05;         // 5% contingency (ICAO)
    trip_fuel + reserve + alternate + contingency
}

// ICAO fuel planning breakdown: (trip, contingency, alternate, final_reserve, total)
function fuel_breakdown_lbs(distance_nm: float, cruise_speed_kts: float, burn_rate_pph: float, headwind_kts: float) -> (float, float, float, float, float) {
    let ground_speed = if cruise_speed_kts - headwind_kts > 50.0 then cruise_speed_kts - headwind_kts else 50.0;
    let flight_hours = distance_nm / ground_speed;
    let trip = flight_hours * burn_rate_pph;
    let contingency = trip * 0.05;
    let alternate = burn_rate_pph * 0.5;        // 30 min
    let final_reserve = burn_rate_pph * 0.75;   // 45 min
    (trip, contingency, alternate, final_reserve, trip + contingency + alternate + final_reserve)
}

// ------------------------------------------------------------------
// Altitude and airspeed calculations
// ------------------------------------------------------------------
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

// ------------------------------------------------------------------
// Wind correction and ground speed
// ------------------------------------------------------------------
function sin_f32(x: float) -> float {
    // Taylor series approximation (12 terms)
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
    let gs = if gs < 0.0 then 0.0 else gs;
    (gs, wca_deg)
}

// ------------------------------------------------------------------
// Descent and wind components
// ------------------------------------------------------------------
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