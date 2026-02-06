from dataclasses import dataclass
import math


# ============================================================
#  Validation Helper
# ============================================================

def _validate_head_dimensions(diameter: float, thickness: float) -> tuple:
    """Validate head dimensions for physical consistency."""
    # Validate diameter
    if diameter is None:
        raise ValueError("Diameter is required and cannot be None.")
    try:
        diameter = float(diameter)
    except (TypeError, ValueError):
        raise ValueError(f"Diameter must be a valid number, got: {diameter}")
    if diameter <= 0:
        raise ValueError(f"Diameter must be positive, got: {diameter} m")
    
    # Validate thickness
    if thickness is None:
        raise ValueError("Thickness is required and cannot be None.")
    try:
        thickness = float(thickness)
    except (TypeError, ValueError):
        raise ValueError(f"Thickness must be a valid number, got: {thickness}")
    if thickness < 0:
        raise ValueError(f"Thickness cannot be negative, got: {thickness} m")
    
    # Check physical consistency
    if thickness >= diameter / 2:
        raise ValueError(
            f"Thickness ({thickness*1000:.1f} mm) must be less than radius ({diameter/2*1000:.1f} mm)."
        )
    
    return diameter, thickness


# ============================================================
#  ASME F&D Head
# ============================================================

@dataclass
class ASMEFDHead:
    diameter: float      # external diameter (m)
    thickness: float     # wall thickness (m)

    def __post_init__(self):
        # Validate dimensions
        self.diameter, self.thickness = _validate_head_dimensions(
            self.diameter, self.thickness
        )
        
        # ASME F&D proportions
        self.major = 1.00   # crown radius / D
        self.minor = 0.06   # knuckle radius / D

        # External radii
        Rc_ext = self.major * self.diameter
        Rk_ext = self.minor * self.diameter
        R_ext  = self.diameter / 2

        # External geometry
        a_ext = Rc_ext - Rk_ext
        b_ext = R_ext - Rk_ext

        rp2_ext = (self.diameter - 2 * Rk_ext) / 2
        hp2_ext = Rc_ext - math.sqrt(a_ext**2 - b_ext**2)

        # Internal radii (thin-wall approximation)
        self.crown_radius   = Rc_ext - self.thickness
        self.knuckle_radius = Rk_ext - self.thickness
        self.radius         = R_ext  - self.thickness

        # Internal circle centers (same as external)
        self.c_height_offset = Rc_ext
        self.c_radius_offset = 0.0

        self.k_height_offset = hp2_ext
        self.k_radius_offset = rp2_ext

        # Transition heights
        self.h1 = 0.0
        alpha_ext = math.asin(rp2_ext / (Rc_ext - Rk_ext))
        self.h2 = Rc_ext - math.cos(alpha_ext) * Rc_ext
        self.h3 = self.k_height_offset


    # --------------------------------------------------------

    def radius_at_height(self, h):
        """Internal radius at height h inside the head."""
        if h <= self.h2:
            val = self.crown_radius**2 - (h - self.c_height_offset)**2
            return math.sqrt(max(val, 0.0)) + self.c_radius_offset

        if h <= self.h3:
            val = self.knuckle_radius**2 - (h - self.k_height_offset)**2
            return math.sqrt(max(val, 0.0)) + self.k_radius_offset

        return self.radius

    def area_at_height(self, h):
        r = self.radius_at_height(h)
        return math.pi * r**2

    def volume_up_to(self, h, steps=500):
        total = 0.0
        dh = (h - self.h1) / steps
        for i in range(steps):
            hi = self.h1 + i * dh
            total += self.area_at_height(hi) * dh
        return total

    def max_head_volume(self):
        return self.volume_up_to(self.h3)


# ============================================================
#  Elliptical 2:1 Head
# ============================================================

@dataclass
class Elliptical2to1Head:
    diameter: float
    thickness: float

    def __post_init__(self):
        # Validate dimensions
        self.diameter, self.thickness = _validate_head_dimensions(
            self.diameter, self.thickness
        )
        
        # ASME 2:1 ellipsoidal proportions
        self.major = 0.90
        self.minor = 0.17

        # External radii
        Rc_ext = self.major * self.diameter
        Rk_ext = self.minor * self.diameter
        R_ext  = self.diameter / 2

        # External geometry
        a_ext = Rc_ext - Rk_ext
        b_ext = R_ext - Rk_ext

        rp2_ext = (self.diameter - 2 * Rk_ext) / 2
        hp2_ext = Rc_ext - math.sqrt(a_ext**2 - b_ext**2)

        # Internal radii
        self.crown_radius   = Rc_ext - self.thickness
        self.knuckle_radius = Rk_ext - self.thickness
        self.radius         = R_ext  - self.thickness

        # Internal circle centers
        self.c_height_offset = Rc_ext
        self.c_radius_offset = 0.0

        self.k_height_offset = hp2_ext
        self.k_radius_offset = rp2_ext

        # Transition heights
        self.h1 = 0.0
        alpha_ext = math.asin(rp2_ext / (Rc_ext - Rk_ext))
        self.h2 = Rc_ext - math.cos(alpha_ext) * Rc_ext
        self.h3 = self.k_height_offset


    # --------------------------------------------------------

    def radius_at_height(self, h):
        if h <= self.h2:
            val = self.crown_radius**2 - (h - self.c_height_offset)**2
            return math.sqrt(max(val, 0.0)) + self.c_radius_offset

        if h <= self.h3:
            val = self.knuckle_radius**2 - (h - self.k_height_offset)**2
            return math.sqrt(max(val, 0.0)) + self.k_radius_offset

        return self.radius

    def area_at_height(self, h):
        r = self.radius_at_height(h)
        return math.pi * r**2

    def volume_up_to(self, h, steps=500):
        total = 0.0
        dh = (h - self.h1) / steps
        for i in range(steps):
            hi = self.h1 + i * dh
            total += self.area_at_height(hi) * dh
        return total

    def max_head_volume(self):
        return self.volume_up_to(self.h3)


# ============================================================
#  Hemispherical Head
# ============================================================

@dataclass
class HemisphericalHead:
    diameter: float
    thickness: float

    def __post_init__(self):
        # Validate dimensions
        self.diameter, self.thickness = _validate_head_dimensions(
            self.diameter, self.thickness
        )
        
        # Internal sphere radius
        self.radius = self.diameter / 2 - self.thickness

        # Hemisphere depth = radius
        self.head_depth = self.radius

        # Integration limits
        self.h1 = 0.0
        self.h2 = self.head_depth

    # --------------------------------------------------------

    def radius_at_height(self, h):
        if h <= self.h2:
            val = self.radius**2 - (self.radius - h)**2
            return math.sqrt(max(val, 0.0))
        return self.radius

    def area_at_height(self, h):
        r = self.radius_at_height(h)
        return math.pi * r**2

    def volume_up_to(self, h, steps=500):
        total = 0.0
        dh = (h - self.h1) / steps
        for i in range(steps):
            hi = self.h1 + i * dh
            total += self.area_at_height(hi) * dh
        return total

    def max_head_volume(self):
        return self.volume_up_to(self.h2)
