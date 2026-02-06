# -----------------------------
# Validation Helper
# -----------------------------

def _safe_float(value, name: str) -> float:
    """Safely convert value to float with helpful error message."""
    if value is None:
        raise ValueError(f"{name} is required and cannot be None.")
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a valid number, got: {value}")


# -----------------------------
# Mass flow conversions
# -----------------------------

def kg_hr_to_lb_hr(m_kg_hr: float) -> float:
    """Convert mass flow from kg/hr to lb/hr."""
    m_kg_hr = _safe_float(m_kg_hr, "Mass flow (kg/hr)")
    if m_kg_hr < 0:
        raise ValueError(f"Mass flow cannot be negative, got: {m_kg_hr} kg/hr")
    return m_kg_hr * 2.2046226218


def lb_hr_to_kg_hr(m_lb_hr: float) -> float:
    """Convert mass flow from lb/hr to kg/hr."""
    m_lb_hr = _safe_float(m_lb_hr, "Mass flow (lb/hr)")
    if m_lb_hr < 0:
        raise ValueError(f"Mass flow cannot be negative, got: {m_lb_hr} lb/hr")
    return m_lb_hr / 2.2046226218


# -----------------------------
# Temperature conversions
# -----------------------------

def C_to_K(T_C: float) -> float:
    """Convert temperature from Celsius to Kelvin."""
    T_C = _safe_float(T_C, "Temperature (°C)")
    if T_C < -273.15:
        raise ValueError(
            f"Temperature cannot be below absolute zero (-273.15°C), got: {T_C}°C"
        )
    return T_C + 273.15


def C_to_R(T_C: float) -> float:
    """Convert temperature from Celsius to Rankine."""
    T_C = _safe_float(T_C, "Temperature (°C)")
    if T_C < -273.15:
        raise ValueError(
            f"Temperature cannot be below absolute zero (-273.15°C), got: {T_C}°C"
        )
    return (T_C + 273.15) * 9.0 / 5.0


def K_to_R(T_K: float) -> float:
    """Convert temperature from Kelvin to Rankine."""
    T_K = _safe_float(T_K, "Temperature (K)")
    if T_K < 0:
        raise ValueError(
            f"Temperature in Kelvin cannot be negative, got: {T_K} K"
        )
    return T_K * 9.0 / 5.0


# -----------------------------
# Pressure conversions
# -----------------------------

def barg_to_psia(P_barg: float) -> float:
    """Convert pressure from barg to psia."""
    P_barg = _safe_float(P_barg, "Pressure (barg)")
    # Absolute pressure must be positive
    P_bara = P_barg + 1.01325
    if P_bara <= 0:
        raise ValueError(
            f"Absolute pressure cannot be zero or negative. "
            f"Got {P_barg} barg = {P_bara:.4f} bara"
        )
    # 1 bar = 14.5037738 psi
    return P_bara * 14.5037738


def psig_to_psia(P_psig: float) -> float:
    """Convert pressure from psig to psia."""
    P_psig = _safe_float(P_psig, "Pressure (psig)")
    P_psia = P_psig + 14.7
    if P_psia <= 0:
        raise ValueError(
            f"Absolute pressure cannot be zero or negative. "
            f"Got {P_psig} psig = {P_psia:.4f} psia"
        )
    return P_psia


# -----------------------------
# Energy conversions
# -----------------------------

def kJ_per_kg_to_J_per_kg(h_kJ_kg: float) -> float:
    """Convert specific enthalpy from kJ/kg to J/kg."""
    h_kJ_kg = _safe_float(h_kJ_kg, "Enthalpy (kJ/kg)")
    if h_kJ_kg < 0:
        raise ValueError(
            f"Enthalpy of vaporization cannot be negative, got: {h_kJ_kg} kJ/kg"
        )
    return h_kJ_kg * 1000.0
