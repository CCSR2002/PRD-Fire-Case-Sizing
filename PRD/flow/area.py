import math


# ============================================================
#  Validation Helpers
# ============================================================

def _validate_k(k: float) -> float:
    """Validate specific heat ratio."""
    if k is None:
        raise ValueError("Specific heat ratio (k) is required.")
    try:
        k = float(k)
    except (TypeError, ValueError):
        raise ValueError(f"Specific heat ratio must be a valid number, got: {k}")
    if k <= 1.0:
        raise ValueError(
            f"Specific heat ratio (k) must be > 1.0 for real gases, got: {k}. "
            f"Typical range is 1.1 to 1.67."
        )
    if k > 2.0:
        raise ValueError(
            f"Specific heat ratio (k) = {k} is unusually high. "
            f"Typical range is 1.1 to 1.67. Please verify input."
        )
    return k


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


def _validate_factor(value: float, name: str, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Validate a correction factor."""
    value = _validate_positive(value, name)
    if value > max_val:
        raise ValueError(f"{name} should not exceed {max_val}, got: {value}")
    return value


# ============================================================
#  API520 GAS/VAPOR COEFFICIENTS
# ============================================================

def C_gas(k: float) -> float:
    """
    API 520 gas/vapor coefficient C (US units).
    k = ratio of specific heats.
    """
    k = _validate_k(k)
    return 520.0 * math.sqrt(
        k * (2.0 / (k + 1.0)) ** ((k + 1.0) / (k - 1.0))
    )


def F2_subcritical(k: float, r: float) -> float:
    """
    API 520 subcritical flow coefficient F2.
    k = ratio of specific heats.
    r = P2 / P1 (absolute backpressure / relieving pressure).
    """
    k = _validate_k(k)
    
    if r is None:
        raise ValueError("Pressure ratio (r) is required.")
    try:
        r = float(r)
    except (TypeError, ValueError):
        raise ValueError(f"Pressure ratio must be a valid number, got: {r}")
    if r <= 0 or r >= 1:
        raise ValueError(
            f"Pressure ratio (r = P2/P1) must be between 0 and 1 for subcritical flow, got: {r}"
        )
    
    num = (k / (k - 1.0)) * (r ** k) * (
        (1.0 - r ** ((k - 1.0) / k)) / (1.0 - r)
    )
    return math.sqrt(num)


# ============================================================
#  REQUIRED AREA — CRITICAL FLOW
# ============================================================

def required_area_critical_gas(
    W_lb_per_hr: float,
    k: float,
    T_R: float,
    Z: float,
    M_lb_per_lbmol: float,
    P1_psia: float,
    Kd: float,
    Kb: float,
    Kc: float,
) -> float:
    """
    Required PSV/RD area for critical gas/vapor flow (API 520, US units).

    W_lb_per_hr       : mass flowrate (lb/hr)
    k                 : specific heat ratio
    T_R               : relieving temperature (°R)
    Z                 : compressibility factor
    M_lb_per_lbmol    : molecular weight (lb/lbmol)
    P1_psia           : relieving pressure (psia)
    Kd, Kb, Kc        : discharge, backpressure, combination factors
    """
    # Validate all inputs
    W_lb_per_hr = _validate_non_negative(W_lb_per_hr, "Mass flowrate (W_lb_per_hr)")
    if W_lb_per_hr == 0:
        return 0.0  # No flow means no area required
    
    k = _validate_k(k)
    T_R = _validate_positive(T_R, "Temperature (°R)")
    
    Z = _validate_positive(Z, "Compressibility factor (Z)")
    if Z > 2.0:
        raise ValueError(
            f"Compressibility factor Z = {Z} is unusually high. "
            f"Typical range is 0.2 to 1.2."
        )
    
    M_lb_per_lbmol = _validate_positive(M_lb_per_lbmol, "Molecular weight (M)")
    P1_psia = _validate_positive(P1_psia, "Relieving pressure (P1_psia)")
    
    Kd = _validate_factor(Kd, "Discharge coefficient (Kd)", 0.0, 1.0)
    Kb = _validate_factor(Kb, "Backpressure factor (Kb)", 0.0, 1.0)
    Kc = _validate_factor(Kc, "Combination factor (Kc)", 0.0, 1.0)
    
    C = C_gas(k)

    num = W_lb_per_hr * math.sqrt(T_R * Z / M_lb_per_lbmol)
    den = C * Kd * P1_psia * Kb * Kc
    
    if den == 0:
        raise ValueError(
            "Denominator is zero - check Kd, Kb, Kc, and P1_psia values."
        )

    return num / den


# ============================================================
#  REQUIRED AREA — SUBCRITICAL FLOW
# ============================================================

def required_area_subcritical_gas(
    W_lb_per_hr: float,
    k: float,
    T_R: float,
    Z: float,
    M_lb_per_lbmol: float,
    P1_psia: float,
    P2_psia: float,
    Kd: float,
    Ke: float,
) -> float:
    """
    Required PSV/RD area for subcritical gas/vapor flow (API 520, US units).

    W_lb_per_hr       : mass flowrate (lb/hr)
    k                 : specific heat ratio
    T_R               : relieving temperature (°R)
    Z                 : compressibility factor
    M_lb_per_lbmol    : molecular weight (lb/lbmol)
    P1_psia           : relieving pressure (psia)
    P2_psia           : backpressure (psia)
    Kd, Ke            : discharge and velocity factors
    """
    # Validate all inputs
    W_lb_per_hr = _validate_non_negative(W_lb_per_hr, "Mass flowrate (W_lb_per_hr)")
    if W_lb_per_hr == 0:
        return 0.0  # No flow means no area required
    
    k = _validate_k(k)
    T_R = _validate_positive(T_R, "Temperature (°R)")
    
    Z = _validate_positive(Z, "Compressibility factor (Z)")
    if Z > 2.0:
        raise ValueError(
            f"Compressibility factor Z = {Z} is unusually high. "
            f"Typical range is 0.2 to 1.2."
        )
    
    M_lb_per_lbmol = _validate_positive(M_lb_per_lbmol, "Molecular weight (M)")
    P1_psia = _validate_positive(P1_psia, "Relieving pressure (P1_psia)")
    P2_psia = _validate_positive(P2_psia, "Backpressure (P2_psia)")
    
    if P2_psia >= P1_psia:
        raise ValueError(
            f"Backpressure ({P2_psia} psia) must be less than relieving pressure ({P1_psia} psia)."
        )
    
    Kd = _validate_factor(Kd, "Discharge coefficient (Kd)", 0.0, 1.0)
    Ke = _validate_factor(Ke, "Environmental factor (Ke)", 0.0, 2.0)  # Ke can exceed 1
    
    r = P2_psia / P1_psia
    F2 = F2_subcritical(k, r)

    pressure_diff = P1_psia - P2_psia
    if pressure_diff <= 0:
        raise ValueError("Pressure difference must be positive for subcritical flow.")
    
    num = W_lb_per_hr * math.sqrt(
        Z * T_R / (M_lb_per_lbmol * P1_psia * pressure_diff)
    )
    den = 735.0 * F2 * Kd * Ke
    
    if den == 0:
        raise ValueError(
            "Denominator is zero - check F2, Kd, and Ke values."
        )

    return num / den


# ============================================================
#  UNIT CONVERSION
# ============================================================

def kg_per_hr_to_lb_per_hr(m_kg_per_hr: float) -> float:
    """Convert kg/hr → lb/hr."""
    return m_kg_per_hr * 2.2046226218
