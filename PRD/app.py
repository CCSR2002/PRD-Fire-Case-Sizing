from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Your actual modules
from sizing.prd import size_psv_for_fire
from geometry.vessel import wetted_area_firecase, wetted_area_from_fill_volume, _build_head
from utils.validation import (
    ValidationError,
    safe_float,
    safe_positive_float,
    safe_non_negative_float,
    validate_choice,
    validate_boolean,
    validate_k_ratio,
    validate_compressibility,
    validate_molecular_weight,
    validate_temperature_celsius,
    validate_correction_factor,
    validate_percentage,
)

app = FastAPI()

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Fire height limits
FIRE_HEIGHT_LIMITS = {
    "API2000": 9.14,   # 30 ft
    "API520": 7.62,    # 25 ft
}

# Valid choices for dropdowns
VALID_FIRE_STANDARDS = ["API2000", "API520"]
VALID_ORIENTATIONS = ["Vertical"]
VALID_HEAD_TYPES = ["ASME_FD", "Ellipsoidal", "Hemispherical"]


def get_field(data: dict, field: str, default=None):
    """Safely get a field from the request data."""
    value = data.get(field, default)
    if value is None or (isinstance(value, str) and value.strip() == ""):
        if default is not None:
            return default
        raise ValidationError(f"Required field '{field}' is missing or empty.")
    return value


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/calculate")
async def calculate(request: Request):
    try:
        # Parse JSON body
        try:
            data = await request.json()
        except Exception:
            return JSONResponse(
                {"error": "Invalid JSON in request body."},
                status_code=400
            )

        if not isinstance(data, dict):
            return JSONResponse(
                {"error": "Request body must be a JSON object."},
                status_code=400
            )

        # Validate fire standard
        fire_standard = validate_choice(
            get_field(data, "fire_standard"),
            "Fire Standard",
            VALID_FIRE_STANDARDS
        )
        fire_height_m = FIRE_HEIGHT_LIMITS.get(fire_standard, 9.14)

        # Validate orientation and head type
        orientation = validate_choice(
            get_field(data, "orientation"),
            "Vessel Orientation",
            VALID_ORIENTATIONS
        )
        head_type = validate_choice(
            get_field(data, "head_type"),
            "Head Type",
            VALID_HEAD_TYPES
        )

        # Validate geometry inputs
        tangent_length_m = safe_non_negative_float(
            get_field(data, "tangent_length_m"),
            "Tangent Length"
        )
        outer_diameter_m = safe_positive_float(
            get_field(data, "outer_diameter_m"),
            "Outer Diameter"
        )
        shell_thickness_mm = safe_non_negative_float(
            get_field(data, "shell_thickness_mm"),
            "Shell Thickness"
        )
        bottom_height_m = safe_non_negative_float(
            get_field(data, "bottom_height_m"),
            "Bottom Height"
        )

        # Validate thickness vs radius
        if shell_thickness_mm / 1000.0 >= outer_diameter_m / 2:
            return JSONResponse(
                {"error": f"Error with Shell Thickness input: {shell_thickness_mm} mm must be less than vessel radius of {outer_diameter_m/2*1000:.1f} mm."},
                status_code=400
            )

        # Validate normal fill volume
        normal_fill_volume_m3 = safe_non_negative_float(
            get_field(data, "normal_fill_volume_m3"),
            "Normal Fill Volume"
        )

        # Validate thermodynamic properties
        h_fg_kJ_per_kg = safe_positive_float(
            get_field(data, "h_fg_kJ_per_kg"),
            "Enthalpy of Vaporization"
        )
        h_fg_J_per_kg = h_fg_kJ_per_kg * 1000.0

        M_g_per_mol = safe_positive_float(
            get_field(data, "M_g_per_mol"),
            "Molecular Weight"
        )
        validate_molecular_weight(M_g_per_mol)
        # Molecular weight: g/mol is numerically equal to lb/lbmol
        M_lb_per_lbmol = M_g_per_mol

        k = safe_positive_float(get_field(data, "k"), "Specific Heat Ratio (k)")
        validate_k_ratio(k)

        Z = safe_positive_float(get_field(data, "Z"), "Compressibility Factor (Z)")
        validate_compressibility(Z)

        T_C = safe_float(get_field(data, "T_C"), "Temperature")
        validate_temperature_celsius(T_C)

        # Validate pressure inputs
        P_operating_psig = safe_float(
            get_field(data, "P_operating_psig"),
            "Operating Pressure"
        )
        # Convert operating pressure from psig to barg for API2000 calculations
        # 1 psi = 0.0689476 bar
        P_design_barg = P_operating_psig * 0.0689476
        
        MAWP_psig = safe_positive_float(
            get_field(data, "MAWP_psig"),
            "MAWP"
        )
        atm_psia = safe_positive_float(
            get_field(data, "atm_psia", 14.7),
            "Atmospheric Pressure"
        )
        backpressure_psig = safe_non_negative_float(
            get_field(data, "backpressure_psig", 0.0),
            "Backpressure"
        )
        accum_percent = safe_positive_float(
            get_field(data, "accum_percent"),
            "Accumulation Percent"
        )
        validate_percentage(accum_percent, "Accumulation Percent")

        # Validate firefighting flag
        firefighting = validate_boolean(
            get_field(data, "firefighting"),
            "Firefighting"
        )

        # Validate correction factors (typically 0-1, but some can exceed 1)
        Kd = safe_positive_float(get_field(data, "Kd"), "Discharge Coefficient (Kd)")
        validate_correction_factor(Kd, "Kd", 0.0, 1.0)

        Kb = safe_positive_float(get_field(data, "Kb"), "Backpressure Factor (Kb)")
        validate_correction_factor(Kb, "Kb", 0.0, 1.0)

        Kc = safe_positive_float(get_field(data, "Kc"), "Combination Factor (Kc)")
        validate_correction_factor(Kc, "Kc", 0.0, 1.0)

        Ke = safe_positive_float(get_field(data, "Ke", 1.0), "Environmental Factor (Ke)")
        validate_correction_factor(Ke, "Ke", 0.0, 2.0)  # Ke can be > 1

        # Auto-switch to API520 if MAWP > 15 psig (API2000 not applicable)
        if MAWP_psig > 15 and fire_standard == "API2000":
            fire_standard = "API520"
            fire_height_m = FIRE_HEIGHT_LIMITS.get(fire_standard, 7.62)

        # Geometry calculation based on normal fill volume
        geometry_result = wetted_area_from_fill_volume(
            orientation=orientation,
            head_type=head_type,
            L_tangent_m=tangent_length_m,
            OD_m=outer_diameter_m,
            thickness_mm=shell_thickness_mm,
            bottom_height_m=bottom_height_m,
            fire_height_m=fire_height_m,
            fill_volume_m3=normal_fill_volume_m3,
        )
        A_wetted_m2 = geometry_result["wetted_area_m2"]
        liquid_height_m = geometry_result["liquid_height_m"]
        liquid_height_exposed_m = geometry_result["liquid_height_exposed_m"]

        # PRD sizing
        result = size_psv_for_fire(
            A_wetted_m2=A_wetted_m2,
            fire_standard=fire_standard,
            P_design_barg=P_design_barg,
            firefighting=firefighting,
            h_fg_J_per_kg=h_fg_J_per_kg,
            k=k,
            Z=Z,
            M_lb_per_lbmol=M_lb_per_lbmol,
            T_C=T_C,
            MAWP_psig=MAWP_psig,
            atm_psia=atm_psia,
            accum_percent=accum_percent,
            backpressure_psig=backpressure_psig,
            Kd=Kd,
            Kb=Kb,
            Kc=Kc,
            Ke=Ke,
        )

        # Add geometry info
        result["A_wetted_m2"] = A_wetted_m2
        result["fire_height_m"] = fire_height_m
        result["liquid_height_m"] = liquid_height_m
        result["liquid_height_exposed_m"] = liquid_height_exposed_m
        result["fire_standard_used"] = fire_standard

        return JSONResponse(result)

    except ValidationError as e:
        # User-friendly validation errors
        return JSONResponse({"error": str(e)}, status_code=400)

    except ValueError as e:
        # Catch domain-specific errors from downstream modules
        return JSONResponse({"error": str(e)}, status_code=400)

    except Exception as e:
        # Log unexpected errors but return a generic message
        print("🔥 Unexpected error in /calculate:", e)
        return JSONResponse(
            {"error": "An unexpected error occurred. Please check your inputs and try again."},
            status_code=500
        )
