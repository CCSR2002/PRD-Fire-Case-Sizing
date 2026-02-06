def heat_load_api520(A_wetted: float, firefighting: bool) -> float:
    """
    API520 fire heat input (Watts) based on wetted surface area and firefighting/drainage status.

    A_wetted: wetted surface area in m²
    firefighting: True if firefighting and drainage is provided, False otherwise
    """
    # Validate wetted area
    if A_wetted is None:
        raise ValueError("Wetted area (A_wetted) is required.")
    try:
        A_wetted = float(A_wetted)
    except (TypeError, ValueError):
        raise ValueError(f"Wetted area must be a valid number, got: {A_wetted}")
    if A_wetted < 0:
        raise ValueError(f"Wetted area cannot be negative, got: {A_wetted} m²")
    if A_wetted == 0:
        return 0.0  # No wetted area means no heat load

    # Validate firefighting flag
    if firefighting is None:
        raise ValueError("Firefighting parameter is required.")
    if not isinstance(firefighting, bool):
        # Try to convert common string values
        if isinstance(firefighting, str):
            lower = firefighting.lower().strip()
            if lower in ("true", "1", "yes"):
                firefighting = True
            elif lower in ("false", "0", "no"):
                firefighting = False
            else:
                raise ValueError(
                    f"Firefighting must be true/false, got: '{firefighting}'"
                )
        else:
            firefighting = bool(firefighting)

    C = 43200 if firefighting else 70900
    return C * A_wetted ** 0.82
