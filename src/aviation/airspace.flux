// airspace.flux – Airspace classes and restricted areas

causal_mosaic airspace_state = sparse_temporal_matrix();

// ------------------------------------------------------------------
// Airspace class (represented as string for simplicity)
// Valid values: "A", "B", "C", "D", "E", "G", "Restricted",
//               "Prohibited", "Warning", "Danger", "Mva", "Tfr"
// ------------------------------------------------------------------
struct Airspace {
    designation: string,
    class: string,
    boundary: [(float, float)],   // list of (latitude, longitude) vertices
    floor_ft: int,
    ceiling_ft: int,
    effective_times: string,
    frequency_mhz: float,
    controller: string,
}

// ------------------------------------------------------------------
// Point-in-polygon algorithm (Ray casting algorithm)
// Returns true if point (lat, lon) is inside the polygon.
// ------------------------------------------------------------------
function point_in_polygon(point: (float, float), polygon: [(float, float)]) -> bool {
    if len(polygon) == 0 {
        return false;
    }
    let (x, y) = point;
    let mut inside = false;
    let mut j = len(polygon) - 1;
    for i in 0..len(polygon) {
        let (xi, yi) = polygon[i];
        let (xj, yj) = polygon[j];
        // Check if the edge straddles the horizontal line at y
        if (yi > y) != (yj > y) {
            // Compute x-coordinate of intersection
            let slope = (x - xi) * (yj - yi) - (xj - xi) * (y - yi);
            if slope == 0.0 {
                // Point lies exactly on the edge
                return true;
            }
            if (slope < 0.0) != (yj < yi) {
                inside = not inside;
            }
        }
        j = i;
    }
    inside
}

// ------------------------------------------------------------------
// Check if a given position violates an airspace.
// Returns true if the point is inside the airspace's vertical and
// horizontal boundaries.
// ------------------------------------------------------------------
function check_airspace_violation(lat: float, lon: float, alt_ft: int, airspace: Airspace) -> bool {
    if alt_ft < airspace.floor_ft or alt_ft > airspace.ceiling_ft {
        return false;
    }
    point_in_polygon((lat, lon), airspace.boundary)
}

// ------------------------------------------------------------------
// Optional: store airspaces in the mosaic and query all violations
// ------------------------------------------------------------------
function store_airspace(designation: string, airspace: Airspace) {
    airspace_state.accept("as_" ++ designation).write(airspace, 1.0);
}

function get_airspace(designation: string) -> Airspace? {
    airspace_state.accept("as_" ++ designation).read() otherwise nil
}

// ------------------------------------------------------------------
// Check all stored airspaces for violation.
// Returns a list of designations that are violated.
// ------------------------------------------------------------------
function find_violating_airspaces(lat: float, lon: float, alt_ft: int) -> [string] {
    let mut violations = [];
    // Retrieve all keys starting with "as_" – requires enumeration capability.
    // For simplicity, we assume a function `list_airspace_keys()` exists or we maintain a separate list.
    // Here we use a manually maintained list (you can extend the mosaic to store a list of keys).
    let keys = airspace_state.accept("airspace_keys").read() otherwise [];
    for key in keys {
        let as = airspace_state.accept(key).read() otherwise continue;
        if check_airspace_violation(lat, lon, alt_ft, as) {
            violations = append(violations, as.designation);
        }
    }
    violations
}