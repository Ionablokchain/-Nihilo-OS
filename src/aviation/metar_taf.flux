// metar.flux – METAR/TAF aviation weather

causal_mosaic weather_state = sparse_temporal_matrix();

// ------------------------------------------------------------------
// Data structures
// ------------------------------------------------------------------
struct Wind {
    direction_deg: u16,
    speed_knots: u16,
    gust_knots: u16,
    variable: bool,
}

struct CloudLayer {
    coverage: string,   // "Few", "Scattered", "Broken", "Overcast", "Clear"
    base_ft: u32,
    kind: string?,      // "Cumulonimbus", "ToweringCumulus" or nil
}

struct Metar {
    icao: string,
    observation_time: u64,
    wind: Wind,
    visibility_meters: u32,
    weather_phenomena: [string],
    clouds: [CloudLayer],
    temperature_c: int,
    dewpoint_c: int,
    altimeter_hpa: u16,
    raw: string,
}

// Flight category as string: "Vfr", "Mvfr", "Ifr", "Lifr"

// ------------------------------------------------------------------
// METAR parser (stub – full implementation would be more complex)
// ------------------------------------------------------------------
function parse_metar(raw: string) -> Metar? {
    let parts = split(raw, " ");
    if len(parts) < 4 {
        return nil;
    }
    // Stub: return a default METAR with raw string
    Metar {
        icao: parts[0],
        observation_time: 0,
        wind: Wind { direction_deg: 0, speed_knots: 0, gust_knots: 0, variable: false },
        visibility_meters: 9999,
        weather_phenomena: [],
        clouds: [],
        temperature_c: 15,
        dewpoint_c: 5,
        altimeter_hpa: 1013,
        raw: raw,
    }
}

// ------------------------------------------------------------------
// Flight category determination
// ------------------------------------------------------------------
function flight_category(metar: Metar) -> string {
    // Find lowest broken or overcast ceiling (base in feet)
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

// ------------------------------------------------------------------
// Helper: store/retrieve METAR for an ICAO code
// ------------------------------------------------------------------
function store_metar(icao: string, metar: Metar) {
    weather_state.accept("metar_" ++ icao).write(metar, 1.0);
}

function get_metar(icao: string) -> Metar? {
    weather_state.accept("metar_" ++ icao).read() otherwise nil
}