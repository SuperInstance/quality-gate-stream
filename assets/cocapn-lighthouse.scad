$fn=32;

module lighthouse_tower() {
    // Tapered concrete base frustum
    color("#555555") {
        cylinder(r1=12, r2=6, h=15);
    }

    // Main cylindrical tower shaft
    color("#777777") {
        translate([0, 0, 15])
        cylinder(r=6, h=25);
    }

    // Glass lantern room at top of tower
    color("#f0f0f0") {
        translate([0, 0, 40])
        cylinder(r=4, h=4);
    }

    // Small central lantern lens cap
    color("white") {
        translate([0, 0, 44])
        cylinder(r=2, h=1);
    }

    // 4 concentric radar rings radiating from lantern height
    color("#4488ff") {
        for(ring_index = [0:3]) {
            // Calculate increasing radii for each concentric ring
            inner_rad = 5 + (3 * ring_index);
            outer_rad = 7 + (3 * ring_index);
            
            // Thin flat ring at lantern midpoint height
            translate([0, 0, 42])
            difference() {
                cylinder(r=outer_rad, h=0.5);
                cylinder(r=inner_rad, h=0.5);
            }
        }
    }
}

// Call the module to render
lighthouse_tower();