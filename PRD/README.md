# PRD Fire-Case Sizing Tool

A web-based pressure relief device (PRD) sizing calculator for fire exposure scenarios, implementing API 2000 and API 520 standards.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. Clone or download the repository

2. Install dependencies:

   ```bash
   pip install fastapi uvicorn jinja2
   ```

3. Run the application:

   ```bash
   cd c:\PRD
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

---

## Fire Heat Load Standards

The tool supports two fire heat load calculation methods that automatically switch based on the Maximum Allowable Working Pressure (MAWP):

### API 2000 (Low-Pressure Vessels)

**Applicable when:** MAWP ≤ 15 psig (1.034 barg)

API 2000 provides fire heat load equations based on wetted surface area and design pressure. The equations vary depending on the wetted area size:

| Wetted Area (m²) | Design Pressure (barg) | Heat Load Formula (Watts) |
| ---------------- | ---------------------- | ------------------------- |
| A < 18.6         | P ≤ 1.034              | Q = 63,150 × A            |
| 18.6 ≤ A < 93    | P ≤ 1.034              | Q = 224,200 × A^0.566     |
| 93 ≤ A < 260     | P ≤ 1.034              | Q = 630,400 × A^0.338     |
| A ≥ 260          | 0.07 ≤ P ≤ 1.034       | Q = 43,200 × A^0.82       |
| A ≥ 260          | P < 0.07               | Q = 4,129,700 (constant)  |

**Fire Height Limit:** 9.14 m (30 ft) above grade

### API 520 (High-Pressure Vessels)

**Applicable when:** MAWP > 15 psig (automatically selected)

API 520 uses the following heat load equation:

$$Q = C \times A_{wetted}^{0.82}$$

Where:

- **Q** = Heat load (Watts)
- **A_wetted** = Wetted surface area (m²)
- **C** = Constant based on firefighting provisions:
  - C = 43,200 W/m² (with prompt firefighting and drainage)
  - C = 70,900 W/m² (without firefighting provisions)

**Fire Height Limit:** 7.62 m (25 ft) above grade

---

## Wetted Area Calculation

The wetted area is calculated based on the **Normal Fill Volume** input, not the total vessel surface area.

### Calculation Process:

1. **Liquid Height from Volume:**
   - The liquid height is determined by solving the volume equation for the vessel geometry (head + cylindrical shell + head)
2. **Exposed Height:**
   - The liquid height exposed to fire is the **minimum** of:
     - Liquid level in vessel
     - Fire height limit minus vessel bottom elevation

3. **Wetted Surface Area:**
   - Integrates the surface area from vessel bottom up to the exposed liquid height
   - Includes bottom head and cylindrical shell contributions

### Vessel Geometry Support:

- **ASME F&D (Flanged & Dished):** Torispherical head
- **Ellipsoidal 2:1:** Elliptical head with 2:1 aspect ratio
- **Hemispherical:** Half-sphere head

---

## Evaporation Rate

The mass evaporation rate is calculated from the fire heat load:

$$\dot{m} = \frac{Q}{\Delta H_{vap}}$$

Where:

- **ṁ** = Evaporation rate (kg/s)
- **Q** = Fire heat load (W)
- **ΔH_vap** = Enthalpy of vaporization (J/kg)

---

## Relieving Pressure

The relieving pressure is calculated per API 520:

$$P_1 = MAWP + Accumulation + P_{atm}$$

Where:

- **P₁** = Relieving pressure (psia)
- **MAWP** = Maximum Allowable Working Pressure (psig)
- **Accumulation** = MAWP × (Accumulation % / 100)
- **P_atm** = Atmospheric pressure (psia)

For fire cases, typical accumulation is **21%** (16% overpressure + 5% tolerance).

---

## Critical vs Subcritical Flow

Flow is **critical** when the downstream pressure is below the critical pressure ratio:

$$P_{crit} = P_1 \times \left(\frac{2}{k+1}\right)^{\frac{k}{k-1}}$$

Where **k** is the specific heat ratio (Cp/Cv).

- If **P_downstream < P_crit**: Critical flow (sonic velocity at throat)
- If **P_downstream ≥ P_crit**: Subcritical flow

---

## Required Orifice Area

### Critical Flow (API 520):

$$A = \frac{W \sqrt{\frac{TZ}{M}}}{C \cdot K_d \cdot P_1 \cdot K_b \cdot K_c}$$

### Subcritical Flow (API 520):

$$A = \frac{W \sqrt{\frac{ZT}{M \cdot P_1 \cdot (P_1 - P_2)}}}{735 \cdot F_2 \cdot K_d \cdot K_e}$$

Where:

- **A** = Required orifice area (in²)
- **W** = Mass flow rate (lb/hr)
- **T** = Temperature (°R)
- **Z** = Compressibility factor
- **M** = Molecular weight (lb/lbmol)
- **P₁** = Relieving pressure (psia)
- **P₂** = Backpressure (psia)
- **C** = Gas constant from specific heat ratio
- **K_d** = Discharge coefficient (typically 0.975)
- **K_b** = Backpressure correction factor
- **K_c** = Combination factor (1.0 for valve only, 0.9 with rupture disk)
- **K_e** = Environmental factor
- **F₂** = Subcritical flow coefficient

---

## API 526 Standard Orifice Designations

| Letter | Effective Area (in²) | Effective Diameter (in) | Standard Inlet Size (in) |
| ------ | -------------------- | ----------------------- | ------------------------ |
| D      | 0.110                | 0.374                   | 1.0                      |
| E      | 0.196                | 0.500                   | 1.0                      |
| F      | 0.307                | 0.625                   | 1.5                      |
| G      | 0.503                | 0.800                   | 1.5                      |
| H      | 0.785                | 1.000                   | 2.0                      |
| J      | 1.287                | 1.280                   | 3.0                      |
| K      | 1.838                | 1.530                   | 3.0                      |
| L      | 2.853                | 1.906                   | 4.0                      |
| M      | 3.600                | 2.141                   | 4.0                      |
| N      | 4.454                | 2.381                   | 4.0                      |
| P      | 6.380                | 2.850                   | 6.0                      |
| Q      | 11.050               | 3.751                   | 6.0                      |
| R      | 16.000               | 4.514                   | 8.0                      |
| T      | 26.000               | 5.753                   | 8.0                      |

---

## Correction Factors

| Factor  | Description             | Typical Value                  |
| ------- | ----------------------- | ------------------------------ |
| **K_d** | Discharge coefficient   | 0.975                          |
| **K_b** | Backpressure correction | 1.0 (balanced bellows)         |
| **K_c** | Combination factor      | 1.0 (PSV only), 0.9 (PSV + RD) |
| **K_e** | Environmental factor    | 1.0 (no insulation)            |

---

## Operating Pressure Recommendation

The tool automatically suggests an **Operating Pressure** equal to **90% of MAWP** when you enter the MAWP value. This follows industry best practice to provide adequate margin between normal operating conditions and the relief set pressure.

---

## Input Summary

### Vessel Geometry

- Orientation (Vertical only, currently)
- Head Type (ASME F&D, Hemispherical, Ellipsoidal)
- Shell Height (tangent-to-tangent length)
- Outer Diameter
- Shell Thickness
- Surface to Vessel Bottom Height
- MAWP (Maximum Allowable Working Pressure)
- Normal Fill Volume

### Relief Line

- Fire Standard (API2000/API520 - auto-selected based on MAWP)
- Operating Pressure
- Firefighting provisions
- Accumulation percentage
- Backpressure

### Fluid Properties

- Specific Heat Ratio (k)
- Enthalpy of Vaporization
- Molecular Weight
- Compressibility Factor (Z)
- Temperature at Relieving Pressure

---

## Output Summary

- **Height at Top of Liquid in Vessel** - Liquid level from vessel bottom
- **Liquid Height Exposed to Fire** - Portion within fire height limit
- **Wetted Surface Area** - Area exposed to fire heat
- **Fire Heat Load Calculation Method** - API2000 or API520
- **Fire Heat Load** - Heat input from fire (kW)
- **Evaporation Rate** - Mass flow of vapor generated
- **Relieving Pressure** - Pressure at valve relief
- **Critical Flow** - Yes/No indicator
- **Required Area** - Minimum orifice area needed
- **Selected Orifice** - Standard API orifice letter designation
- **Minimum Inlet Size** - Recommended pipe size

---

## References

- API Standard 2000: _Venting Atmospheric and Low-Pressure Storage Tanks_
- API Standard 520 Part I: _Sizing, Selection, and Installation of Pressure-Relieving Devices_
- API Standard 521: _Pressure-Relieving and Depressuring Systems_
- ASME Boiler and Pressure Vessel Code, Section VIII

---

## License

This tool is provided for educational and engineering estimation purposes. Always verify calculations with qualified engineers and applicable codes before implementation.
