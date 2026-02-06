from fire.api2000 import heat_load_api2000
from fire.api520 import heat_load_api520

from flow.evaporation import evaporation_rate_kg_per_hr
from flow.area import required_area_critical_gas, required_area_subcritical_gas
from flow.pressures import (
    max_accumulation,
    relieving_pressure,
    critical_downstream_pressure,
    downstream_pressure,
)

from sizing.orifice import select_orifice
from utils.units import kg_hr_to_lb_hr, C_to_R


# ============================================================
#  VALIDATION HELPERS
# ============================================================

VALID_FIRE_STANDARDS = ["API2000", "API520"]


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


# ============================================================
#  FIRE HEAT LOAD DISPATCHER
# ============================================================

def fire_heat_load(
    standard: str,
    A_wetted_m2: float,
    P_design_barg: float,
    firefighting: bool
) -> float:
    """
    Dispatches to API2000 or API520 fire heat load calculation.
    Returns heat load in Watts.
    """
    # Validate standard
    if standard is None or not isinstance(standard, str):
        raise ValueError("Fire sizing standard is required.")
    if standard not in VALID_FIRE_STANDARDS:
        raise ValueError(
            f"Unknown fire sizing standard: '{standard}'. "
            f"Valid options are: {VALID_FIRE_STANDARDS}"
        )
    
    # Validate wetted area
    A_wetted_m2 = _validate_non_negative(A_wetted_m2, "Wetted area (A_wetted_m2)")
    
    if standard == "API2000":
        return heat_load_api2000(A_wetted_m2, P_design_barg)

    if standard == "API520":
        return heat_load_api520(A_wetted_m2, firefighting)

    # Should not reach here due to validation above
    raise ValueError(f"Unknown fire sizing standard: {standard}")


# ============================================================
#  CRITICALITY DECISION
# ============================================================

def is_critical_flow(
    P1_psia: float,
    P_back_psig: float,
    atm_psia: float,
    k: float
) -> bool:
    """
    Determines if flow is critical using API520 critical downstream pressure.
    """
    # Validation is done in the called functions
    P_crit = critical_downstream_pressure(P1_psia, k)
    P_down = downstream_pressure(P_back_psig, atm_psia)
    return P_crit > P_down


# ============================================================
#  MASTER FIRE-CASE PSV SIZING FUNCTION
# ============================================================

def size_psv_for_fire(
    A_wetted_m2: float,
    fire_standard: str,
    P_design_barg: float,
    firefighting: bool,
    h_fg_J_per_kg: float,
    k: float,
    Z: float,
    M_lb_per_lbmol: float,
    T_C: float,
    MAWP_psig: float,
    atm_psia: float,
    accum_percent: float,
    backpressure_psig: float,
    Kd: float,
    Kb: float,
    Kc: float,
    Ke: float,
):
    """
    Full fire-case PSV sizing pipeline:

    1. Fire heat load (W)
    2. Evaporation rate (kg/hr)
    3. Relieving pressure (psia)
    4. Criticality check
    5. Required PSV area (in²)
    6. Orifice selection
    
    All inputs are validated at this top level and in downstream functions.
    """

    # --------------------------------------------------------
    # Validate critical inputs upfront for better error messages
    # --------------------------------------------------------
    A_wetted_m2 = _validate_non_negative(A_wetted_m2, "Wetted area (A_wetted_m2)")
    h_fg_J_per_kg = _validate_positive(h_fg_J_per_kg, "Enthalpy of vaporization (h_fg_J_per_kg)")
    
    # Validate k (specific heat ratio)
    k = _validate_positive(k, "Specific heat ratio (k)")
    if k <= 1.0:
        raise ValueError(
            f"Specific heat ratio (k) must be > 1.0 for real gases, got: {k}"
        )
    
    # Validate Z (compressibility)
    Z = _validate_positive(Z, "Compressibility factor (Z)")
    
    # Validate molecular weight
    M_lb_per_lbmol = _validate_positive(M_lb_per_lbmol, "Molecular weight (M)")
    
    # Validate pressures
    MAWP_psig = _validate_positive(MAWP_psig, "MAWP (psig)")
    atm_psia = _validate_positive(atm_psia, "Atmospheric pressure (psia)")
    backpressure_psig = _validate_non_negative(backpressure_psig, "Backpressure (psig)")
    accum_percent = _validate_positive(accum_percent, "Accumulation percent")
    
    # Validate correction factors
    Kd = _validate_positive(Kd, "Discharge coefficient (Kd)")
    Kb = _validate_positive(Kb, "Backpressure factor (Kb)")
    Kc = _validate_positive(Kc, "Combination factor (Kc)")
    Ke = _validate_positive(Ke, "Environmental factor (Ke)")

    # --------------------------------------------------------
    # 1) Fire heat load (W)
    # --------------------------------------------------------
    Q_dot_W = fire_heat_load(
        fire_standard,
        A_wetted_m2,
        P_design_barg,
        firefighting
    )

    # --------------------------------------------------------
    # 2) Evaporation rate (kg/hr)
    # --------------------------------------------------------
    m_kg_hr = evaporation_rate_kg_per_hr(Q_dot_W, h_fg_J_per_kg)

    # Convert to lb/hr for API520 equations
    W_lb_hr = kg_hr_to_lb_hr(m_kg_hr)

    # Convert temperature to Rankine
    T_R = C_to_R(T_C)

    # --------------------------------------------------------
    # 3) Relieving pressure (psia)
    # --------------------------------------------------------
    accum_psig = max_accumulation(MAWP_psig, accum_percent)
    P1_psia = relieving_pressure(MAWP_psig, atm_psia, accum_psig)

    # --------------------------------------------------------
    # 4) Criticality check
    # --------------------------------------------------------
    critical = is_critical_flow(P1_psia, backpressure_psig, atm_psia, k)

    # --------------------------------------------------------
    # 5) Required PSV area (in²)
    # --------------------------------------------------------
    if critical:
        A_req = required_area_critical_gas(
            W_lb_hr, k, T_R, Z, M_lb_per_lbmol, P1_psia, Kd, Kb, Kc
        )
    else:
        P2_psia = downstream_pressure(backpressure_psig, atm_psia)
        A_req = required_area_subcritical_gas(
            W_lb_hr, k, T_R, Z, M_lb_per_lbmol, P1_psia, P2_psia, Kd, Ke
        )

    # --------------------------------------------------------
    # 6) Orifice selection
    # --------------------------------------------------------
    orifice = select_orifice(A_req)

    return {
        "Q_dot_W": Q_dot_W,
        "m_kg_hr": m_kg_hr,
        "W_lb_hr": W_lb_hr,
        "P1_psia": P1_psia,
        "critical": critical,
        "A_required_in2": A_req,
        "orifice_letter": orifice["letter"],
        "orifice_area_in2": orifice["area_in2"],
        "orifice_diameter_in": orifice["diameter_in"],
        "inlet_size_in": orifice["inlet_size_in"],
    }
