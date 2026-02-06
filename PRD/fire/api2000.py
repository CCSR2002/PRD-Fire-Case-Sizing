def heat_load_api2000(A_wetted_m2: float, P_design_barg: float) -> float:
    """
    API2000 fire heat load (Watts) from wetted area (m²) and design pressure (barg).
    Automatically falls back to API520-style heat flux for P > 1.034 barg.
    """

    # Validate inputs
    if A_wetted_m2 is None:
        raise ValueError("Wetted area (A_wetted_m2) is required.")
    try:
        A_wetted_m2 = float(A_wetted_m2)
    except (TypeError, ValueError):
        raise ValueError(f"Wetted area must be a valid number, got: {A_wetted_m2}")
    if A_wetted_m2 < 0:
        raise ValueError(f"Wetted area cannot be negative, got: {A_wetted_m2} m²")
    if A_wetted_m2 == 0:
        return 0.0  # No wetted area means no heat load

    if P_design_barg is None:
        raise ValueError("Design pressure (P_design_barg) is required.")
    try:
        P_design_barg = float(P_design_barg)
    except (TypeError, ValueError):
        raise ValueError(f"Design pressure must be a valid number, got: {P_design_barg}")

    # -----------------------------------------
    # HIGH-PRESSURE CASE → NOT COVERED BY API2000
    # -----------------------------------------
    if P_design_barg > 1.034:
        # API 520 fire heat flux (approx 10800 W/m²)
        # This is the standard fallback used in industry
        return 10800.0 * A_wetted_m2

    # -----------------------------------------
    # LOW-PRESSURE CASES (API2000 TABLE)
    # -----------------------------------------

    # Row 1: A < 18.6 m², P ≤ 1.034 barg
    if A_wetted_m2 < 18.6:
        return 63150 * A_wetted_m2

    # Row 2: 18.6 ≤ A < 93 m², P ≤ 1.034 barg
    if 18.6 <= A_wetted_m2 < 93:
        return 224200 * (A_wetted_m2 ** 0.566)

    # Row 3: 93 ≤ A < 260 m², P ≤ 1.034 barg
    if 93 <= A_wetted_m2 < 260:
        return 630400 * (A_wetted_m2 ** 0.338)

    # Row 4: A ≥ 260 m², 0.07 ≤ P ≤ 1.034 barg
    if A_wetted_m2 >= 260 and P_design_barg >= 0.07:
        return 43200 * (A_wetted_m2 ** 0.82)

    # Row 5: A ≥ 260 m², P ≤ 0.07 barg
    if A_wetted_m2 >= 260 and P_design_barg < 0.07:
        return 4129700.0

    # Should never reach here
    raise ValueError(
        f"Unexpected API2000 input combination: A={A_wetted_m2}, P={P_design_barg}"
    )
