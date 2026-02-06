import math

# API orifice table (area in square inches)
API_ORIFICES = {
    "D": 0.110,
    "E": 0.196,
    "F": 0.307,
    "G": 0.503,
    "H": 0.785,
    "J": 1.287,
    "K": 1.838,
    "L": 2.853,
    "M": 3.600,
    "N": 4.454,
    "P": 6.380,
    "Q": 11.050,
    "R": 16.000,
    "T": 26.000,
}

# API standard inlet sizes (in inches) for each orifice letter
# Based on API 526 standard flange sizes
API_INLET_SIZES = {
    "D": 1.0,
    "E": 1.0,
    "F": 1.5,
    "G": 1.5,
    "H": 2.0,
    "J": 3.0,
    "K": 3.0,
    "L": 4.0,
    "M": 4.0,
    "N": 4.0,
    "P": 6.0,
    "Q": 6.0,
    "R": 8.0,
    "T": 8.0,
}

# Maximum available orifice area
MAX_ORIFICE_AREA = max(API_ORIFICES.values())


def get_orifice_diameter(area_in2: float) -> float:
    """Calculate effective orifice diameter from area."""
    return 2.0 * math.sqrt(area_in2 / math.pi)


def select_orifice(A_required_in2: float) -> dict:
    """
    Returns the smallest API orifice letter that meets or exceeds the required area.
    Returns a descriptive message if no standard orifice is large enough.
    """
    # Validate input
    if A_required_in2 is None:
        raise ValueError("Required area is missing.")
    
    try:
        A_required_in2 = float(A_required_in2)
    except (TypeError, ValueError):
        raise ValueError(f"Required area must be a valid number, got: {A_required_in2}")
    
    if A_required_in2 < 0:
        raise ValueError(f"Required area cannot be negative, got: {A_required_in2} in²")
    
    if A_required_in2 == 0:
        # Return smallest orifice for zero area requirement
        return {
            "letter": "D",
            "area_in2": API_ORIFICES["D"],
            "diameter_in": get_orifice_diameter(API_ORIFICES["D"]),
            "inlet_size_in": API_INLET_SIZES["D"],
        }
    
    # Find suitable orifice
    for letter, area in sorted(API_ORIFICES.items(), key=lambda x: x[1]):
        if area >= A_required_in2:
            return {
                "letter": letter,
                "area_in2": area,
                "diameter_in": get_orifice_diameter(area),
                "inlet_size_in": API_INLET_SIZES[letter],
            }
    
    # If no orifice is large enough, provide helpful message
    raise ValueError(
        f"No standard API orifice can accommodate required area: {A_required_in2:.3f} in². "
        f"Maximum available is 'T' at {MAX_ORIFICE_AREA} in². "
        f"Consider multiple relief devices or a rupture disc."
    )
