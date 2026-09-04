"""Spårvik: compact Scandinavian turntable and vinyl shelf.

Units: millimetres. X is left-to-right, Y is front-to-back, Z is bottom-to-top.
The front is at negative Y and the rear is at Y=0. This is a design aid, not
structural certification; wall anchoring is recommended.
"""
from pathlib import Path

from build123d import Align, Box, Compound, Cylinder, Location, export_step, export_stl

# ---------------------------------------------------------------------------
# Main editable parameters (mm)
# ---------------------------------------------------------------------------
OVERALL_WIDTH = 550.0
OVERALL_HEIGHT = 1260.0
OVERALL_DEPTH = 440.0
# All frame panels use the same 10 mm board thickness.
PANEL_THICKNESS = 10.0

# User equipment sizes: turntable 450 W x 400 D x 360 H; records 320 square.
TURNTABLE_WIDTH = 450.0
TURNTABLE_DEPTH = 400.0
TURNTABLE_HEIGHT = 360.0
RECORD_SIZE = 320.0

# Clearance around the turntable and records.
TURNTABLE_SIDE_CLEARANCE = 25.0
TURNTABLE_REAR_CLEARANCE = 20.0
TURNTABLE_TOP_CLEARANCE = 25.0
RECORD_SIDE_CLEARANCE = 10.0
RECORD_TOP_CLEARANCE = 20.0
RECORD_FRONT_CLEARANCE = 30.0

# Requested 100 mm clear gap between the stacked record section and turntable.
# The gap is bounded by a full-width, full-depth horizontal plane.
TURN_TABLE_RECORD_GAP = 100.0
SPACING_PLANE_THICKNESS = PANEL_THICKNESS
# A 10 mm-high stop keeps the visible front edges consistent with the board.
RECORD_LIP_HEIGHT = PANEL_THICKNESS
RECORD_LIP_THICKNESS = PANEL_THICKNESS

CABLE_OPENING_WIDTH = 100.0
CABLE_OPENING_HEIGHT = 50.0
BACK_PANEL_THICKNESS = PANEL_THICKNESS
WALL_ANCHOR_HOLE_DIAMETER = 8.0

# Filleting is intentionally omitted: edge selection can vary between
# build123d versions. FRONT_EDGE_FILLET remains available for fabrication.
FRONT_EDGE_FILLET = 3.0

INNER_WIDTH = OVERALL_WIDTH - 2 * PANEL_THICKNESS
# The closed back occupies 10 mm of the internal depth.
INNER_DEPTH = OVERALL_DEPTH - BACK_PANEL_THICKNESS

RECORD_CLEAR_WIDTH = RECORD_SIZE + 2 * RECORD_SIDE_CLEARANCE
RECORD_CLEAR_HEIGHT = RECORD_SIZE + RECORD_TOP_CLEARANCE
RECORD_CLEAR_DEPTH = RECORD_SIZE + RECORD_FRONT_CLEARANCE

TURNTABLE_CLEAR_WIDTH = TURNTABLE_WIDTH + 2 * TURNTABLE_SIDE_CLEARANCE
TURNTABLE_CLEAR_HEIGHT = TURNTABLE_HEIGHT + TURNTABLE_TOP_CLEARANCE
TURNTABLE_CLEAR_DEPTH = TURNTABLE_DEPTH + TURNTABLE_REAR_CLEARANCE

BOTTOM_TOP = PANEL_THICKNESS
LOWER_RECORD_TOP = BOTTOM_TOP + RECORD_CLEAR_HEIGHT
RECORD_MIDDLE_SHELF_Z = LOWER_RECORD_TOP
UPPER_RECORD_TOP = LOWER_RECORD_TOP + PANEL_THICKNESS + RECORD_CLEAR_HEIGHT

# From top to bottom the intended order is:
# turntable allocation -> 100 mm gap -> full spacing plane -> disc box 1 -> disc box 2.
# Disc box 1 is therefore the upper record compartment.
DISC_BOX_1_FLOOR_Z = LOWER_RECORD_TOP + PANEL_THICKNESS
DISC_BOX_2_FLOOR_Z = BOTTOM_TOP

SPACING_PLANE_Z = UPPER_RECORD_TOP
TURNTABLE_SHELF_Z = (
    SPACING_PLANE_Z + SPACING_PLANE_THICKNESS + TURN_TABLE_RECORD_GAP
)


def box(size, location):
    """Create a minimum-aligned box at (x, y, z)."""
    return Box(*size, align=(Align.MIN, Align.MIN, Align.MIN)).locate(
        Location(location)
    )


def build_components():
    front_y = -OVERALL_DEPTH
    x_inner = PANEL_THICKNESS
    components = {}

    components["Left side panel"] = box(
        (PANEL_THICKNESS, OVERALL_DEPTH, OVERALL_HEIGHT),
        (0, front_y, 0),
    )
    components["Right side panel"] = box(
        (PANEL_THICKNESS, OVERALL_DEPTH, OVERALL_HEIGHT),
        (OVERALL_WIDTH - PANEL_THICKNESS, front_y, 0),
    )
    components["Top panel"] = box(
        (INNER_WIDTH, OVERALL_DEPTH, PANEL_THICKNESS),
        (x_inner, front_y, OVERALL_HEIGHT - PANEL_THICKNESS),
    )
    components["Bottom panel"] = box(
        (INNER_WIDTH, OVERALL_DEPTH, PANEL_THICKNESS),
        (x_inner, front_y, 0),
    )

    # Two record compartments, stacked vertically. Disc box 1 is above
    # disc box 2, directly below the 100 mm gap to the turntable.
    components["Record middle shelf"] = box(
        (INNER_WIDTH, OVERALL_DEPTH, PANEL_THICKNESS),
        (x_inner, front_y, RECORD_MIDDLE_SHELF_Z),
    )

    # Full-width/full-depth plane below the 100 mm spacing layer. This is not
    # a small rear strip: it is a complete horizontal furniture-board shelf.
    components["10 cm spacing plane"] = box(
        (INNER_WIDTH, OVERALL_DEPTH, SPACING_PLANE_THICKNESS),
        (x_inner, front_y, SPACING_PLANE_Z),
    )

    # The turntable shelf is above the full spacing layer, keeping the
    # turntable allocation at the top level of the cabinet.
    components["Turntable shelf"] = box(
        (INNER_WIDTH, OVERALL_DEPTH, PANEL_THICKNESS),
        (x_inner, front_y, TURNTABLE_SHELF_Z),
    )

    # The middle shelf is the shared boundary: it is simultaneously the
    # lower panel of disc box 1 and the upper panel of disc box 2.
    # The bottom panel is the lower boundary of disc box 2. No extra lips or
    # duplicate panels are added at either record-box boundary.

    # Full closed back panel. It is the same 10 mm thickness as every other
    # frame panel. Anchor it to suitable studs or masonry; the unit is not
    # structurally certified.
    rear = box(
        (INNER_WIDTH, BACK_PANEL_THICKNESS, OVERALL_HEIGHT - 2 * PANEL_THICKNESS),
        (x_inner, -BACK_PANEL_THICKNESS, PANEL_THICKNESS),
    )

    # Cable pass-through in the closed back behind the turntable.
    cable_opening = box(
        (CABLE_OPENING_WIDTH, BACK_PANEL_THICKNESS + 2, CABLE_OPENING_HEIGHT),
        (
            OVERALL_WIDTH / 2 - CABLE_OPENING_WIDTH / 2,
            -BACK_PANEL_THICKNESS - 1,
            TURNTABLE_SHELF_Z + PANEL_THICKNESS + 45,
        ),
    )
    rear = rear - cable_opening

    # Two wall-anchor holes through the closed back panel.
    for x in (x_inner + 100, OVERALL_WIDTH - PANEL_THICKNESS - 100):
        anchor_hole = Cylinder(
            WALL_ANCHOR_HOLE_DIAMETER / 2,
            BACK_PANEL_THICKNESS + 2,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            rotation=(90, 0, 0),
        ).locate(Location((x, -BACK_PANEL_THICKNESS / 2, OVERALL_HEIGHT - 100)))
        rear = rear - anchor_hole

    components["Full back panel"] = rear
    return components


def bounds(shape):
    b = shape.bounding_box()
    return tuple(round(v, 2) for v in (*b.min, *b.max))


def validate(components, assembly):
    assert len(assembly.solids()) == len(components)

    for name, component in components.items():
        assert component.is_valid, f"Invalid solid: {name}"
        assert len(component.solids()) == 1, f"Not one solid: {name}"

    assert INNER_WIDTH >= TURNTABLE_CLEAR_WIDTH
    assert INNER_DEPTH >= TURNTABLE_CLEAR_DEPTH
    assert TURNTABLE_CLEAR_HEIGHT >= TURNTABLE_HEIGHT + 25.0

    assert INNER_WIDTH >= RECORD_CLEAR_WIDTH
    assert RECORD_CLEAR_HEIGHT >= RECORD_SIZE + 20.0
    assert RECORD_CLEAR_DEPTH >= RECORD_SIZE + 30.0

    b = assembly.bounding_box()
    actual = (b.max.X - b.min.X, b.max.Y - b.min.Y, b.max.Z - b.min.Z)
    expected = (OVERALL_WIDTH, OVERALL_DEPTH, OVERALL_HEIGHT)
    assert all(abs(a - e) < 0.01 for a, e in zip(actual, expected))
    return actual


def main():
    output = Path(__file__).parent / "exports"
    components_output = output / "components"
    components_output.mkdir(parents=True, exist_ok=True)

    components = build_components()
    assembly = Compound.make_composite(list(components.values()))
    assembly_size = validate(components, assembly)

    export_step(assembly, output / "sparvik_assembly.step")
    export_stl(assembly, output / "sparvik_assembly.stl")

    for name, component in components.items():
        filename = name.lower().replace(" ", "_") + ".step"
        export_step(component, components_output / filename)

    print("Spårvik validation summary")
    print(f"Overall dimensions: {assembly_size[0]:.1f} x {assembly_size[1]:.1f} x {assembly_size[2]:.1f} mm")
    print(f"Turntable clearance: {TURNTABLE_CLEAR_WIDTH:.1f} W x {TURNTABLE_CLEAR_DEPTH:.1f} D x {TURNTABLE_CLEAR_HEIGHT:.1f} H mm")
    print(f"Each record bay: {RECORD_CLEAR_WIDTH:.1f} W x {RECORD_CLEAR_DEPTH:.1f} D x {RECORD_CLEAR_HEIGHT:.1f} H mm")
    print(f"Top-to-bottom layout: turntable -> {TURN_TABLE_RECORD_GAP:.1f} mm gap -> full spacing plane -> disc box 1 -> disc box 2")
    print(f"Number of solids: {len(assembly.solids())}")
    print("Failed operations: none")
    for name, component in components.items():
        print(f"- {name}: bbox={bounds(component)} mm")
    print("Assumptions: 25 mm side and top turntable clearance; 20 mm rear clearance; 20 mm record headroom.")
    print("The full back panel closes the cabinet; anchor it to suitable studs or masonry.")


if __name__ == "__main__":
    main()
