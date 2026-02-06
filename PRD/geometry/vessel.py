import math
from geometry.heads import ASMEFDHead, Elliptical2to1Head, HemisphericalHead


# ------------------------------------------------------------
# Input Validation Helpers
# ------------------------------------------------------------

def _validate_positive(value: float, name: str) -> float:
    """Validate that a value is positive."""
    if value is None:
        raise ValueError(f"{name} is required and cannot be None.")
    try:
        val = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a valid number, got: {value}")
    if val <= 0:
        raise ValueError(f"{name} must be positive, got: {val}")
    return val


def _validate_non_negative(value: float, name: str) -> float:
    """Validate that a value is non-negative."""
    if value is None:
        raise ValueError(f"{name} is required and cannot be None.")
    try:
        val = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a valid number, got: {value}")
    if val < 0:
        raise ValueError(f"{name} must be non-negative, got: {val}")
    return val


def _validate_positive_int(value: int, name: str, min_val: int = 1) -> int:
    """Validate that a value is a positive integer."""
    try:
        val = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a valid integer, got: {value}")
    if val < min_val:
        raise ValueError(f"{name} must be at least {min_val}, got: {val}")
    return val


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def wetted_area_firecase(
    orientation: str,
    head_type: str,
    L_tangent_m: float,
    OD_m: float,
    thickness_mm: float,
    bottom_height_m: float,
    fire_height_m: float,
    steps: int = 500,
) -> float:
    """
    Fire-case wetted area for a vertical vessel.

    Uses:
      - head_type: "ASME_FD", "Ellipsoidal", "Hemispherical"
      - OD_m: external diameter (m)
      - thickness_mm: shell/head thickness (mm)
      - L_tangent_m: tangent-to-tangent length (m)
      - bottom_height_m: vessel bottom elevation above grade (m)
      - fire_height_m: flame height above grade (m)

    Returns wetted area (m²) from vessel bottom up to the fire height.
    """

    # Validate orientation
    if orientation is None or not isinstance(orientation, str):
        raise ValueError("Vessel orientation is required and must be a string.")
    if orientation != "Vertical":
        raise ValueError(
            f"Only 'Vertical' orientation is supported, got: '{orientation}'. "
            f"Horizontal vessels are not yet implemented."
        )

    # Validate head type
    valid_head_types = ["ASME_FD", "Ellipsoidal", "Hemispherical"]
    if head_type not in valid_head_types:
        raise ValueError(
            f"Head type must be one of {valid_head_types}, got: '{head_type}'"
        )

    # Validate dimensions
    OD_m = _validate_positive(OD_m, "Outer diameter (OD_m)")
    thickness_mm = _validate_non_negative(thickness_mm, "Wall thickness (thickness_mm)")
    L_tangent_m = _validate_non_negative(L_tangent_m, "Tangent length (L_tangent_m)")
    bottom_height_m = _validate_non_negative(bottom_height_m, "Bottom height (bottom_height_m)")
    fire_height_m = _validate_non_negative(fire_height_m, "Fire height (fire_height_m)")
    steps = _validate_positive_int(steps, "Integration steps", min_val=10)

    # Check thickness vs radius
    thickness_m = thickness_mm / 1000.0
    if thickness_m >= OD_m / 2:
        raise ValueError(
            f"Wall thickness ({thickness_mm} mm) must be less than radius ({OD_m/2*1000:.1f} mm)."
        )

    head = _build_head(head_type, OD_m, thickness_mm)

    # Liquid height measured from vessel bottom
    H_liquid = fire_height_m - bottom_height_m
    if H_liquid <= 0:
        return 0.0

    # Clamp to total vessel height (bottom head + shell + top head)
    H_head = getattr(head, "h3", head.h2)
    H_total = H_head + L_tangent_m + H_head
    H_liquid = min(H_liquid, H_total)

    return wetted_area_up_to_height(H_liquid, head, L_tangent_m, steps)


def wetted_area_from_volume(
    V_m3: float,
    head,
    shell_height_m: float,
    steps: int = 500,
) -> float:
    """
    Total wetted area (m²) of a vertical vessel given a liquid volume (m³).
    Includes bottom head, cylindrical shell, and top head.
    """

    # Validate inputs
    V_m3 = _validate_non_negative(V_m3, "Volume (V_m3)")
    shell_height_m = _validate_non_negative(shell_height_m, "Shell height (shell_height_m)")
    steps = _validate_positive_int(steps, "Integration steps", min_val=10)

    if head is None:
        raise ValueError("Head object is required and cannot be None.")

    H = liquid_height_from_volume(V_m3, head, shell_height_m)
    return wetted_area_up_to_height(H, head, shell_height_m, steps)


def wetted_area_from_fill_volume(
    orientation: str,
    head_type: str,
    L_tangent_m: float,
    OD_m: float,
    thickness_mm: float,
    bottom_height_m: float,
    fire_height_m: float,
    fill_volume_m3: float,
    steps: int = 500,
) -> dict:
    """
    Calculate wetted area for fire case based on normal fill volume.
    
    The wetted area is the surface area of the vessel wetted by liquid,
    limited by the fire height above grade.
    
    Returns a dict with:
      - liquid_height_m: total height of liquid in vessel from vessel bottom
      - liquid_height_exposed_m: height of liquid exposed to fire
      - wetted_area_m2: wetted surface area exposed to fire (m²)
    """
    
    # Validate orientation
    if orientation is None or not isinstance(orientation, str):
        raise ValueError("Vessel orientation is required and must be a string.")
    if orientation != "Vertical":
        raise ValueError(
            f"Only 'Vertical' orientation is supported, got: '{orientation}'. "
            f"Horizontal vessels are not yet implemented."
        )

    # Validate head type
    valid_head_types = ["ASME_FD", "Ellipsoidal", "Hemispherical"]
    if head_type not in valid_head_types:
        raise ValueError(
            f"Head type must be one of {valid_head_types}, got: '{head_type}'"
        )

    # Validate dimensions
    OD_m = _validate_positive(OD_m, "Error with Outer Diameter input")
    thickness_mm = _validate_non_negative(thickness_mm, "Error with Shell Thickness input")
    L_tangent_m = _validate_non_negative(L_tangent_m, "Error with Shell Height input")
    bottom_height_m = _validate_non_negative(bottom_height_m, "Error with Surface to Vessel Bottom Height input")
    fire_height_m = _validate_non_negative(fire_height_m, "Error with Fire Height input")
    fill_volume_m3 = _validate_non_negative(fill_volume_m3, "Error with Normal Fill Volume input")
    steps = _validate_positive_int(steps, "Integration steps", min_val=10)

    # Check thickness vs radius
    thickness_m = thickness_mm / 1000.0
    if thickness_m >= OD_m / 2:
        raise ValueError(
            f"Wall thickness ({thickness_mm} mm) must be less than radius ({OD_m/2*1000:.1f} mm)."
        )

    head = _build_head(head_type, OD_m, thickness_mm)
    H_head = getattr(head, "h3", head.h2)
    H_total = H_head + L_tangent_m + H_head
    
    # Calculate maximum vessel volume
    V_head = head.max_head_volume()
    R = head.radius
    A_cyl = math.pi * R**2
    V_max = V_head * 2 + A_cyl * L_tangent_m  # Both heads + cylinder
    
    # Validate fill volume doesn't exceed vessel capacity
    if fill_volume_m3 > V_max:
        raise ValueError(
            f"Error with Normal Fill Volume input: Volume of {fill_volume_m3:.3f} m³ exceeds "
            f"vessel capacity of {V_max:.3f} m³. Please enter a smaller fill volume."
        )
    
    # Calculate liquid height from fill volume
    liquid_height_m = liquid_height_from_volume(fill_volume_m3, head, L_tangent_m)
    
    # The liquid level measured from grade (ground level)
    liquid_level_from_grade = bottom_height_m + liquid_height_m
    
    # Fire height limit from grade
    # The wetted area exposed to fire is from vessel bottom to min(liquid level, fire height)
    fire_limit_from_vessel_bottom = fire_height_m - bottom_height_m
    
    if fire_limit_from_vessel_bottom <= 0:
        # Fire doesn't reach the vessel
        return {
            "liquid_height_m": liquid_height_m,
            "liquid_height_exposed_m": 0.0,
            "wetted_area_m2": 0.0,
        }
    
    # Exposed liquid height is limited by both liquid level and fire height
    liquid_height_exposed_m = min(liquid_height_m, fire_limit_from_vessel_bottom)
    
    # Calculate wetted area up to the exposed liquid height
    wetted_area_m2 = wetted_area_up_to_height(liquid_height_exposed_m, head, L_tangent_m, steps)
    
    return {
        "liquid_height_m": liquid_height_m,
        "liquid_height_exposed_m": liquid_height_exposed_m,
        "wetted_area_m2": wetted_area_m2,
    }


# ------------------------------------------------------------
# Head construction
# ------------------------------------------------------------

def _build_head(head_type: str, OD_m: float, thickness_mm: float):
    """
    Factory for head objects based on head_type string.
    Uses OD in m and thickness in mm (converted to m).
    """

    # Validate inputs
    if head_type is None or not isinstance(head_type, str):
        raise ValueError("Head type is required and must be a string.")

    OD_m = _validate_positive(OD_m, "Outer diameter (OD_m)")
    thickness_mm = _validate_non_negative(thickness_mm, "Wall thickness (thickness_mm)")

    thickness_m = thickness_mm / 1000.0

    # Check physical consistency
    if thickness_m >= OD_m / 2:
        raise ValueError(
            f"Wall thickness ({thickness_mm} mm) must be less than radius ({OD_m/2*1000:.1f} mm)."
        )

    if head_type == "ASME_FD":
        return ASMEFDHead(diameter=OD_m, thickness=thickness_m)
    elif head_type == "Ellipsoidal":
        return Elliptical2to1Head(diameter=OD_m, thickness=thickness_m)
    elif head_type == "Hemispherical":
        return HemisphericalHead(diameter=OD_m, thickness=thickness_m)
    else:
        valid_types = ["ASME_FD", "Ellipsoidal", "Hemispherical"]
        raise ValueError(
            f"Unsupported head type: '{head_type}'. Valid types are: {valid_types}"
        )


# ------------------------------------------------------------
# Core wetted area logic
# ------------------------------------------------------------

def wetted_area_up_to_height(
    H: float,
    head,
    shell_height: float,
    steps: int = 500,
) -> float:
    """
    Wetted area (m²) up to a given liquid height H from vessel bottom.
    """

    # Validate inputs
    if head is None:
        raise ValueError("Head object is required and cannot be None.")
    
    try:
        H = float(H)
    except (TypeError, ValueError):
        raise ValueError(f"Height (H) must be a valid number, got: {H}")
    
    if H < 0:
        return 0.0  # Gracefully return 0 for negative heights
    
    try:
        shell_height = float(shell_height)
    except (TypeError, ValueError):
        raise ValueError(f"Shell height must be a valid number, got: {shell_height}")

    if shell_height < 0:
        raise ValueError("shell_height must be non-negative.")

    R = head.radius
    H_head = getattr(head, "h3", head.h2)  # h3 for torispherical, h2 for hemispherical
    H_shell = shell_height

    # Case 1: liquid entirely inside bottom head
    if H <= H_head:
        return head_wetted_area_up_to(H, head, steps)

    # Case 2: bottom head full, liquid in cylinder
    if H <= H_head + H_shell:
        A_head_bottom = head_wetted_area_up_to(H_head, head, steps)
        h_cyl = H - H_head
        A_cyl = 2 * math.pi * R * h_cyl
        return A_head_bottom + A_cyl

    # Case 3: cylinder full, liquid in top head
    A_head_bottom = head_wetted_area_up_to(H_head, head, steps)
    A_cyl = 2 * math.pi * R * H_shell

    h_in_top = H - (H_head + H_shell)
    A_head_top = head_wetted_area_up_to(h_in_top, head, steps)

    return A_head_bottom + A_cyl + A_head_top


# ------------------------------------------------------------
# Liquid height from volume
# ------------------------------------------------------------

def liquid_height_from_volume(
    V_m3: float,
    head,
    shell_height_m: float,
) -> float:
    """
    Total liquid height (m) from vessel bottom for a given volume (m³).
    """

    V_head = head.max_head_volume()
    A_cyl = math.pi * head.radius**2
    H_head = getattr(head, "h3", head.h2)
    H_shell = shell_height_m

    # Case 1: volume entirely in bottom head
    if V_m3 <= V_head:
        return solve_height_in_head(V_m3, head)

    # Case 2: bottom head full, volume in cylinder
    V_rem = V_m3 - V_head
    if V_rem <= A_cyl * H_shell:
        h_cyl = V_rem / A_cyl
        return H_head + h_cyl

    # Case 3: cylinder full, volume in top head
    V_rem -= A_cyl * H_shell
    h_in_top = solve_height_in_head(V_rem, head)

    return H_head + H_shell + h_in_top


# ------------------------------------------------------------
# Solve height in head for partial volume
# ------------------------------------------------------------

def solve_height_in_head(
    V_target: float,
    head,
    steps: int = 40,
) -> float:
    """
    Height inside a head (m) that corresponds to a given volume (m³).
    Binary search between h1 and h3 (or h2 for hemispherical).
    """

    low = head.h1
    high = getattr(head, "h3", head.h2)

    for _ in range(steps):
        mid = 0.5 * (low + high)
        V_mid = head.volume_up_to(mid)

        if V_mid < V_target:
            low = mid
        else:
            high = mid

    return 0.5 * (low + high)


# ------------------------------------------------------------
# Wetted area of head up to height h
# ------------------------------------------------------------

def head_wetted_area_up_to(
    h: float,
    head,
    steps: int = 500,
) -> float:
    """
    Wetted surface area (m²) of a head from h1 up to height h
    using surface-of-revolution integration.
    """

    h_low = head.h1
    h_high = min(h, getattr(head, "h3", head.h2))

    if h <= h_low:
        return 0.0

    dh = (h_high - h_low) / steps
    total = 0.0

    for i in range(steps):
        hi = h_low + i * dh

        r = head.radius_at_height(hi)

        h_forward = min(hi + 1e-5, h_high)
        r_forward = head.radius_at_height(h_forward)
        dr_dh = (r_forward - r) / (h_forward - hi) if h_forward != hi else 0.0

        dA = 2 * math.pi * r * math.sqrt(1 + dr_dh**2) * dh
        total += dA

    return total