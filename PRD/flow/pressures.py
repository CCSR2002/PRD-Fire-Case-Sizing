def _validate_positive(value: float, name: str) -> float:
    """Validate that a value is positive."""
    if value is None:
        raise ValueError(f"{name} is required.")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a valid number, got: {value}")
    if value <= 0:
        raise ValueError(f"{name} must be positive, got: {value}")
    return value


def _validate_non_negative(value: float, name: str) -> float:
    """Validate that a value is non-negative."""
    if value is None:
        raise ValueError(f"{name} is required.")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a valid number, got: {value}")
    if value < 0:
        raise ValueError(f"{name} cannot be negative, got: {value}")
    return value


def max_accumulation(MAWP_psig: float, accumulation_percent: float) -> float:
    """
    Maximum allowable accumulation (psig) based on MAWP and accumulation %.
    """
    MAWP_psig = _validate_positive(MAWP_psig, "MAWP (psig)")
    accumulation_percent = _validate_non_negative(accumulation_percent, "Accumulation percent")
    
    if accumulation_percent > 100:
        raise ValueError(
            f"Accumulation percent should not exceed 100%, got: {accumulation_percent}%"
        )
    
    return MAWP_psig * (accumulation_percent / 100.0)


def relieving_pressure(MAWP_psig: float, atm_psia: float, accumulation_psig: float) -> float:
    """
    Relieving pressure (psia) = MAWP + accumulation + atmospheric pressure.
    """
    MAWP_psig = _validate_positive(MAWP_psig, "MAWP (psig)")
    atm_psia = _validate_positive(atm_psia, "Atmospheric pressure (psia)")
    accumulation_psig = _validate_non_negative(accumulation_psig, "Accumulation (psig)")
    
    return MAWP_psig + accumulation_psig + atm_psia


def critical_downstream_pressure(P1_psia: float, k: float) -> float:
    """
    API 520 critical downstream pressure (psia).
    P1_psia : relieving pressure (psia)
    k       : specific heat ratio
    """
    P1_psia = _validate_positive(P1_psia, "Relieving pressure (P1_psia)")
    
    if k is None:
        raise ValueError("Specific heat ratio (k) is required.")
    try:
        k = float(k)
    except (TypeError, ValueError):
        raise ValueError(f"Specific heat ratio must be a valid number, got: {k}")
    if k <= 1.0:
        raise ValueError(
            f"Specific heat ratio (k) must be > 1.0 for real gases, got: {k}"
        )
    
    ratio = (2.0 / (k + 1.0)) ** (k / (k - 1.0))
    return ratio * P1_psia


def downstream_pressure(P_back_psig: float, atm_psia: float) -> float:
    """
    Absolute downstream pressure (psia) = backpressure (psig) + atmospheric pressure.
    """
    P_back_psig = _validate_non_negative(P_back_psig, "Backpressure (psig)")
    atm_psia = _validate_positive(atm_psia, "Atmospheric pressure (psia)")
    
    return P_back_psig + atm_psia


def is_critical(P1_psia: float, P_back_psig: float, atm_psia: float, k: float) -> bool:
    """
    Determines if flow is critical based on API 520 criteria.
    """
    P_crit = critical_downstream_pressure(P1_psia, k)
    P_down = downstream_pressure(P_back_psig, atm_psia)
    return P_crit > P_down

