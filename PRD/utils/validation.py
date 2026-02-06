"""
Input validation utilities for safe parameter handling.
All validation functions return (value, error_message) tuples.
If validation passes, error_message is None.
If validation fails, value is a default and error_message describes the issue.
"""

from typing import Any, Optional, Tuple, List


class ValidationError(Exception):
    """Custom exception for validation errors with user-friendly messages."""
    pass


def safe_float(value: Any, name: str, default: float = 0.0) -> float:
    """
    Safely convert a value to float.
    Returns the float value or raises ValidationError with a descriptive message.
    """
    if value is None:
        raise ValidationError(f"Error with {name} input: This field is required and cannot be empty.")
    
    try:
        result = float(value)
        return result
    except (ValueError, TypeError):
        raise ValidationError(f"Error with {name} input: Must be a valid number, got '{value}'")


def safe_positive_float(value: Any, name: str, allow_zero: bool = False) -> float:
    """
    Safely convert a value to a positive float.
    """
    result = safe_float(value, name)
    
    if allow_zero:
        if result < 0:
            raise ValidationError(f"Error with {name} input: Must be non-negative, got {result}")
    else:
        if result <= 0:
            raise ValidationError(f"Error with {name} input: Must be positive, got {result}")
    
    return result


def safe_non_negative_float(value: Any, name: str) -> float:
    """
    Safely convert a value to a non-negative float (>= 0).
    """
    return safe_positive_float(value, name, allow_zero=True)


def safe_int(value: Any, name: str, default: int = 0) -> int:
    """
    Safely convert a value to integer.
    """
    if value is None:
        raise ValidationError(f"Error with {name} input: This field is required and cannot be empty.")
    
    try:
        result = int(value)
        return result
    except (ValueError, TypeError):
        raise ValidationError(f"Error with {name} input: Must be a valid integer, got '{value}'")


def safe_positive_int(value: Any, name: str, min_value: int = 1) -> int:
    """
    Safely convert a value to a positive integer with minimum value.
    """
    result = safe_int(value, name)
    
    if result < min_value:
        raise ValidationError(f"Error with {name} input: Must be at least {min_value}, got {result}")
    
    return result


def validate_in_range(
    value: float, 
    name: str, 
    min_val: Optional[float] = None, 
    max_val: Optional[float] = None,
    min_inclusive: bool = True,
    max_inclusive: bool = True
) -> float:
    """
    Validate that a value is within a specified range.
    """
    if min_val is not None:
        if min_inclusive:
            if value < min_val:
                raise ValidationError(f"{name} must be >= {min_val}, got: {value}")
        else:
            if value <= min_val:
                raise ValidationError(f"{name} must be > {min_val}, got: {value}")
    
    if max_val is not None:
        if max_inclusive:
            if value > max_val:
                raise ValidationError(f"{name} must be <= {max_val}, got: {value}")
        else:
            if value >= max_val:
                raise ValidationError(f"{name} must be < {max_val}, got: {value}")
    
    return value


def validate_choice(value: Any, name: str, valid_choices: List[str]) -> str:
    """
    Validate that a value is one of the allowed choices.
    """
    if value is None:
        raise ValidationError(f"{name} is required and cannot be empty.")
    
    str_value = str(value)
    
    if str_value not in valid_choices:
        choices_str = ", ".join(f"'{c}'" for c in valid_choices)
        raise ValidationError(
            f"{name} must be one of [{choices_str}], got: '{str_value}'"
        )
    
    return str_value


def validate_boolean(value: Any, name: str) -> bool:
    """
    Safely convert a value to boolean.
    Handles strings like "true", "false", "1", "0", etc.
    """
    if value is None:
        raise ValidationError(f"{name} is required and cannot be empty.")
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, (int, float)):
        return bool(value)
    
    if isinstance(value, str):
        lower = value.lower().strip()
        if lower in ("true", "1", "yes", "on"):
            return True
        if lower in ("false", "0", "no", "off"):
            return False
        raise ValidationError(
            f"{name} must be a boolean value (true/false), got: '{value}'"
        )
    
    raise ValidationError(f"{name} must be a boolean value, got: '{value}'")


def validate_string_not_empty(value: Any, name: str) -> str:
    """
    Validate that a value is a non-empty string.
    """
    if value is None:
        raise ValidationError(f"{name} is required and cannot be empty.")
    
    str_value = str(value).strip()
    
    if not str_value:
        raise ValidationError(f"{name} cannot be empty.")
    
    return str_value


# ============================================================
#  DOMAIN-SPECIFIC VALIDATORS
# ============================================================

def validate_k_ratio(k: float) -> float:
    """
    Validate specific heat ratio (k = Cp/Cv).
    Must be > 1.0 for all real gases.
    """
    if k <= 1.0:
        raise ValidationError(
            f"Specific heat ratio (k) must be > 1.0, got: {k}. "
            f"For most gases, k is between 1.1 and 1.67."
        )
    if k > 2.0:
        raise ValidationError(
            f"Specific heat ratio (k) = {k} is unusually high. "
            f"Typical range is 1.1 to 1.67. Please verify input."
        )
    return k


def validate_compressibility(Z: float) -> float:
    """
    Validate compressibility factor (Z).
    Must be positive, typically between 0.2 and 1.2.
    """
    if Z <= 0:
        raise ValidationError(
            f"Error with Compressibility Factor (Z) input: Must be positive, got {Z}"
        )
    if Z > 2.0:
        raise ValidationError(
            f"Error with Compressibility Factor (Z) input: Value of {Z} is unusually high. "
            f"Typical range is 0.2 to 1.2. Please verify."
        )
    return Z


def validate_molecular_weight(M: float) -> float:
    """
    Validate molecular weight.
    Must be positive, typically between 2 (H2) and 500.
    """
    if M <= 0:
        raise ValidationError(
            f"Error with Molecular Weight input: Must be positive, got {M}"
        )
    if M < 1:
        raise ValidationError(
            f"Error with Molecular Weight input: Value of {M} is too low. Minimum is ~2 for hydrogen."
        )
    return M


def validate_temperature_celsius(T_C: float) -> float:
    """
    Validate temperature in Celsius.
    Must be above absolute zero.
    """
    if T_C < -273.15:
        raise ValidationError(
            f"Error with Temperature input: Cannot be below absolute zero (-273.15°C), got {T_C}°C"
        )
    return T_C


def validate_pressure_positive(P: float, name: str) -> float:
    """
    Validate that a pressure value is positive.
    """
    if P <= 0:
        raise ValidationError(f"{name} must be positive, got: {P}")
    return P


def validate_correction_factor(K: float, name: str, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Validate a correction factor (Kd, Kb, Kc, Ke, etc.).
    Typically between 0 and 1.
    """
    if K < min_val or K > max_val:
        raise ValidationError(
            f"{name} must be between {min_val} and {max_val}, got: {K}"
        )
    return K


def validate_percentage(value: float, name: str) -> float:
    """
    Validate a percentage value (0-100).
    """
    if value < 0 or value > 100:
        raise ValidationError(
            f"Error with {name} input: Must be between 0 and 100%, got {value}%"
        )
    return value


def validate_vessel_dimensions(
    OD_m: float,
    thickness_mm: float,
    L_tangent_m: float
) -> Tuple[float, float, float]:
    """
    Validate vessel dimensions for physical consistency.
    """
    if OD_m <= 0:
        raise ValidationError(f"Outer diameter must be positive, got: {OD_m} m")
    
    if thickness_mm < 0:
        raise ValidationError(f"Wall thickness cannot be negative, got: {thickness_mm} mm")
    
    # Check that thickness is less than radius
    thickness_m = thickness_mm / 1000.0
    if thickness_m >= OD_m / 2:
        raise ValidationError(
            f"Wall thickness ({thickness_mm} mm) cannot be >= radius ({OD_m/2*1000} mm)"
        )
    
    if L_tangent_m < 0:
        raise ValidationError(f"Tangent length cannot be negative, got: {L_tangent_m} m")
    
    return OD_m, thickness_mm, L_tangent_m
