def evaporation_rate(Q_dot_W: float, h_fg_J_per_kg: float) -> float:
    """
    Computes evaporation rate (kg/s) from heat load (W) and enthalpy of vaporization (J/kg).

    Q_dot_W          : fire heat load in Watts
    h_fg_J_per_kg    : enthalpy of vaporization in J/kg
    """
    # Validate heat load
    if Q_dot_W is None:
        raise ValueError("Heat load (Q_dot_W) is required.")
    try:
        Q_dot_W = float(Q_dot_W)
    except (TypeError, ValueError):
        raise ValueError(f"Heat load must be a valid number, got: {Q_dot_W}")
    if Q_dot_W < 0:
        raise ValueError(f"Heat load cannot be negative, got: {Q_dot_W} W")
    if Q_dot_W == 0:
        return 0.0  # No heat load means no evaporation

    # Validate enthalpy of vaporization
    if h_fg_J_per_kg is None:
        raise ValueError("Enthalpy of vaporization (h_fg_J_per_kg) is required.")
    try:
        h_fg_J_per_kg = float(h_fg_J_per_kg)
    except (TypeError, ValueError):
        raise ValueError(f"Enthalpy of vaporization must be a valid number, got: {h_fg_J_per_kg}")
    if h_fg_J_per_kg <= 0:
        raise ValueError(
            f"Enthalpy of vaporization must be positive, got: {h_fg_J_per_kg} J/kg. "
            f"Typical values range from 100,000 to 2,500,000 J/kg."
        )

    return Q_dot_W / h_fg_J_per_kg


def evaporation_rate_kg_per_hr(Q_dot_W: float, h_fg_J_per_kg: float) -> float:
    """
    Computes evaporation rate in kg/hr.
    Wrapper around evaporation_rate().
    """
    return evaporation_rate(Q_dot_W, h_fg_J_per_kg) * 3600.0
