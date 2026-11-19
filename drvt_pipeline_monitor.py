import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="DRVT Oil & Gas Pipeline Monitor",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Custom Styling
# ---------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 2.0rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .stage-box {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: #F8FAFC;
        padding: 14px;
        border-radius: 10px;
        text-align: center;
        border-bottom: 4px solid #0284C7;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Physics & Chemo-Resonant Engine (DRVT for Pipelines)
# ---------------------------------------------------------
def compute_chemo_drvt_metrics(
    f0_ghz: float,
    q0: float,
    wall_thickness_mm: float,
    pipe_grade: str,
    temp_c: float,
    pressure_bar: float,
    ph: float,
    h2s_ppm: float,
    co2_mol_pct: float,
    chlorides_ppm: float,
    water_cut_pct: float,
    inhibitor_eff_pct: float,
    exposure_months: float
):
    """
    Couples internal fluid electrochemistry (H2S, CO2, pH, Cl-, Water Cut)
    with Dynamic Resonant Volume Theory (DRVT) waveguide/cavity sensing.
    """
    grade_factors = {
        "API 5L X52 (Carbon Steel)": 1.00,
        "API 5L X65 (High-Strength CS)": 1.12,
        "API 5L X70 (Sour Service)": 0.85,
        "Duplex Stainless Steel 2205": 0.25,
    }
    mat_factor = grade_factors.get(pipe_grade, 1.0)

    wetting_factor = np.clip((water_cut_pct / 30.0) ** 1.15, 0.05, 2.5)

    acidity_factor = np.exp((6.8 - ph) * 0.55)
    co2_partial_bar = pressure_bar * (co2_mol_pct / 100.0)
    co2_rate = 0.35 * (co2_partial_bar ** 0.62) * acidity_factor
    h2s_rate = 0.0045 * (h2s_ppm ** 0.72) * (1.0 + 0.015 * max(0.0, temp_c - 25.0))
    chloride_pitting_factor = 1.0 + (chlorides_ppm / 50000.0) * 0.85

    mitigation = 1.0 - (inhibitor_eff_pct / 100.0) * 0.90

    corrosion_rate_mmy = (
        (co2_rate + h2s_rate) * mat_factor * wetting_factor * chloride_pitting_factor * mitigation
    )
    corrosion_rate_mmy = float(np.clip(corrosion_rate_mmy, 0.01, 12.0))

    wall_loss_mm = corrosion_rate_mmy * (exposure_months / 12.0)
    remaining_wall_mm = max(0.5, wall_thickness_mm - wall_loss_mm)
    wall_loss_pct = (wall_loss_mm / wall_thickness_mm) * 100.0

    scale_index = np.clip(
        ((h2s_ppm / 600.0) * 0.45 + (max(0.0, ph - 6.5) / 2.5) * 0.35 + (temp_c / 120.0) * 0.20)
        * (exposure_months / 12.0),
        0.0,
        1.5
    )

    thermal_shift_ghz = -0.00018 * (temp_c - 25.0) * f0_ghz

    dv_rel_wall = (wall_loss_mm / wall_thickness_mm) * 1.45
    dv_rel_scale = -0.045 * scale_index
    dv_rel_net = dv_rel_wall + dv_rel_scale

    pitting_dispersion = (chlorides_ppm / 100000.0) * (wall_loss_pct / 10.0) * 8.0
    rod_shift_pct = (abs(dv_rel_wall) * 100.0 * 1.35) + (scale_index * 9.5) + pitting_dispersion

    q_degradation = 1.0 + (wall_loss_pct * 0.045) + (scale_index * 0.38) + (h2s_ppm / 2500.0)
    q_loaded = max(50.0, q0 / q_degradation)

    f_resonant_ghz = f0_ghz * (1.0 - 0.5 * dv_rel_net) + thermal_shift_ghz

    scii = 100.0 - (rod_shift_pct * 1.65) - (max(0.0, corrosion_rate_mmy - 0.15) * 6.5)
    scii = float(np.clip(scii, 0.0, 100.0))

    if scii >= 82.0 and corrosion_rate_mmy < 0.20:
        status = "NOMINAL / PASSIVATED"
        severity = "Low"
        dominant_mechanism = "Stable Passivation Layer (No Active Degradation)"
    elif h2s_ppm >= 250 and ph < 5.8:
        status = "CRITICAL: SOUR H2S & SSC RISK"
        severity = "Critical"
        dominant_mechanism = "Sour Corrosion (H2S) + Sulfide Stress Cracking (SSC) Hazard"
    elif wall_loss_pct >= 18.0 or corrosion_rate_mmy >= 1.2:
        status = "HIGH RISK: SEVERE WALL THINNING"
        severity = "High"
        dominant_mechanism = "Accelerated CO2/Acidic Internal Wall Loss"
    elif scale_index >= 0.65 and wall_loss_pct < 12.0:
        status = "WARNING: FOULING / FeS SCALE BUILDUP"
        severity = "Moderate"
        dominant_mechanism = "Dielectric/Conductive Scale Deposition Shifting Cavity ROD"
    elif chlorides_ppm >= 40000 and water_cut_pct >= 35:
        status = "WARNING: LOCALIZED CHLORIDE PITTING"
        severity = "High"
        dominant_mechanism = "High-Salinity Localized Pitting & Q-Factor Damping"
    else:
        status = "MODERATE: MONITOR & OPTIMIZE DOSING"
        severity = "Moderate"
        dominant_mechanism = "Gradual Electro-Chemical Drift"

    return {
        "corrosion_rate_mmy": corrosion_rate_mmy,
        "wall_loss_mm": wall_loss_mm,
        "remaining_wall_mm": remaining_wall_mm,
        "wall_loss_pct": wall_loss_pct,
        "scale_index": scale_index,
        "dv_rel_pct": dv_rel_net * 100.0,
        "rod_shift_pct": rod_shift_pct,
        "q_loaded": q_loaded,
        "f_resonant_ghz": f_resonant_ghz,
        "thermal_shift_mhz": thermal_shift_ghz * 1000.0,
        "scii": scii,
        "status": status,
        "severity": severity,
        "dominant_mechanism": dominant_mechanism,
    }


def generate_recommendations(res: dict, h2s_ppm: float, co2_mol_pct: float, ph: float, inhibitor_eff_pct: float, scale_index: float):
    """Generates dual Chemical Treatment & Mechanical NDT recommendations."""
    chem_actions = []
    mech_actions = []

    if h2s_ppm >= 150:
        chem_actions.append(
            f"Inject **H2S Scavenger (Triazine-based)** and film-forming amine inhibitor; current H2S ({h2s_ppm:.0f} ppm) elevates Sulfide Stress Cracking (SSC) risk."
        )
    if co2_mol_pct >= 2.0 or ph < 5.6:
        chem_actions.append(
            f"Increase **pH Stabilizer / Neutralizing Amine** and imidazoline corrosion inhibitor dosing to suppress carbonic acid (H₂CO₃) attack (pH = {ph:.2f})."
        )
    if scale_index >= 0.55:
        chem_actions.append(
            "Dose **Phosphonate / Polymeric Scale Inhibitor** or schedule batch chemical cleaning to dissolve conductive FeS / CaCO₃ deposits."
        )
    if inhibitor_eff_pct < 75.0 and res["corrosion_rate_mmy"] > 0.25:
        chem_actions.append(
            f"Optimize corrosion inhibitor residual concentration (current efficiency {inhibitor_eff_pct:.0f}% is insufficient for active fluid chemistry)."
        )
    if not chem_actions:
        chem_actions.append("Maintain current chemical injection rate; fluid chemistry remains within passivated operating envelope.")

    if res["scii"] < 55.0 or res["wall_loss_pct"] >= 15.0:
        mech_actions.append(
            "**Immediate Action:** Deploy phased-array Ultrasonic Testing (PAUT) at high-ROD resonant nodes and schedule Intelligent Pigging (MFL/UT)."
        )
    elif res["scii"] < 80.0:
        mech_actions.append(
            "**Scheduled Action:** Increase DRVT microwave sensor polling frequency and verify weld joints downstream of injection points."
        )
    else:
        mech_actions.append(
            "**Routine Monitoring:** Continue automated continuous DRVT resonance logging with standard periodic NDT calibration."
        )

    return chem_actions, mech_actions


def build_inspection_plan(res: dict, h2s_ppm: float, co2_mol_pct: float, ph: float, water_cut_pct: float, pipe_length_km: float):
    """
    Determines recommended inspection point spacing, sampling interval,
    and critical locations along the pipeline based on SCII and chemo-resonant risk.
    """
    scii = res["scii"]
    rate = res["corrosion_rate_mmy"]
    scale_idx = res["scale_index"]

    # Base spacing (meters) and polling interval based on SCII & corrosion rate
    if scii < 55.0 or rate >= 1.0:
        straight_spacing_m = 25
        critical_spacing_m = 5
        polling_interval = "Every 5 min (Continuous High-Alert)"
        risk_tier = "Tier-1 Critical (Dense Nodal Mapping)"
    elif scii < 75.0 or rate >= 0.45:
        straight_spacing_m = 50
        critical_spacing_m = 10
        polling_interval = "Every 15 min"
        risk_tier = "Tier-2 Elevated (Targeted Zone Density)"
    elif scii < 88.0 or rate >= 0.20:
        straight_spacing_m = 100
        critical_spacing_m = 25
        polling_interval = "Every 1 hour"
        risk_tier = "Tier-3 Moderate (Standard Risk-Based)"
    else:
        straight_spacing_m = 250
        critical_spacing_m = 50
        polling_interval = "Every 6 hours"
        risk_tier = "Tier-4 Nominal (Baseline Surveillance)"

    estimated_straight_points = int((pipe_length_km * 1000.0) / straight_spacing_m) + 1

    # Prioritize critical point types along pipeline
    points_rows = []

    if water_cut_pct >= 15.0 or rate >= 0.25:
        points_rows.append({
            "Location Type": "Low Points / Sag Bends (Free Water & FeS)",
            "Primary Risk": "Bottom-of-line corrosion, pitting & FeS accumulation",
            "Suggested Spacing": f"Every {critical_spacing_m} m at sag troughs",
            "Sampling / Polling": polling_interval,
            "Verification Method": "DRVT Cavity + Spot UT / PAUT"
        })

    points_rows.append({
        "Location Type": "Downstream of Chemical Injection Quills",
        "Primary Risk": "Incomplete inhibitor/scavenger mixing or local over/under-dosing",
        "Suggested Spacing": f"At 2D, 5D, 15D & {critical_spacing_m*2} m downstream",
        "Sampling / Polling": polling_interval,
        "Verification Method": "DRVT ROD/Q Monitor + Fluid Sampling"
    })

    points_rows.append({
        "Location Type": "Elbows, Tees & Flow Disturbances",
        "Primary Risk": "Elevated wall shear stress & protective film erosion",
        "Suggested Spacing": f"Every {critical_spacing_m} m across bend/extrados",
        "Sampling / Polling": polling_interval,
        "Verification Method": "DRVT Cavity + Ultrasonic Thickness (UT)"
    })

    if h2s_ppm >= 100 or ph < 5.8:
        points_rows.append({
            "Location Type": "Welds & Heat-Affected Zones (HAZ)",
            "Primary Risk": "Sulfide Stress Cracking (SSC) & weld preferential attack",
            "Suggested Spacing": f"Every {critical_spacing_m} m on high-stress welds",
            "Sampling / Polling": polling_interval,
            "Verification Method": "PAUT / Shear-Wave + DRVT Shift"
        })

    if co2_mol_pct >= 1.5 or h2s_ppm >= 50:
        points_rows.append({
            "Location Type": "High Points / Crests (Vapor Condensation)",
            "Primary Risk": "Top-of-Line Corrosion (TLC) from acidic condensate",
            "Suggested Spacing": f"Every {critical_spacing_m*2} m at elevation crests",
            "Sampling / Polling": polling_interval,
            "Verification Method": "DRVT Crown Sensor + UT"
        })

    if scale_idx >= 0.45:
        points_rows.append({
            "Location Type": "Thermal & Pressure Transition Zones",
            "Primary Risk": "Scale precipitation (CaCO₃ / FeS) & cavity volume shift",
            "Suggested Spacing": f"Every {critical_spacing_m*2} m along gradient zones",
            "Sampling / Polling": polling_interval,
            "Verification Method": "DRVT ΔV_eff / Q-Factor + Pigging Log"
        })

    points_rows.append({
        "Location Type": "Straight Pipe Runs (Baseline Grid)",
        "Primary Risk": "General wall thinning & trend drift verification",
        "Suggested Spacing": f"Every {straight_spacing_m} m (~{estimated_straight_points} nodes / {pipe_length_km:.1f} km)",
        "Sampling / Polling": polling_interval,
        "Verification Method": "DRVT Continuous Telemetry"
    })

    return {
        "risk_tier": risk_tier,
        "straight_spacing_m": straight_spacing_m,
        "critical_spacing_m": critical_spacing_m,
        "polling_interval": polling_interval,
        "estimated_straight_points": estimated_straight_points,
        "schedule_df": pd.DataFrame(points_rows)
    }


def generate_sample_csv() -> bytes:
    """Creates a realistic 60-step field telemetry dataset for pipeline chemical-resonance monitoring."""
    np.random.seed(42)
    n = 60
    timestamps = pd.date_range("2026-11-01 00:00", periods=n, freq="6h")

    h2s = np.concatenate([
        np.random.normal(35, 5, 25),
        np.linspace(45, 420, 20) + np.random.normal(0, 12, 20),
        np.linspace(380, 90, 15) + np.random.normal(0, 8, 15)
    ])
    co2 = np.concatenate([
        np.random.normal(1.2, 0.1, 25),
        np.linspace(1.4, 3.8, 20),
        np.linspace(3.5, 1.8, 15)
    ])
    ph = np.concatenate([
        np.random.normal(6.6, 0.08, 25),
        np.linspace(6.5, 5.1, 20),
        np.linspace(5.2, 6.2, 15)
    ])
    chlorides = np.random.normal(28000, 1500, n)
    water_cut = np.concatenate([
        np.random.normal(18, 2, 25),
        np.linspace(22, 48, 20),
        np.linspace(46, 30, 15)
    ])
    temp_c = 45.0 + 4.0 * np.sin(np.linspace(0, 4 * np.pi, n)) + np.random.normal(0, 0.5, n)
    pressure_bar = np.random.normal(62.0, 1.5, n)
    inhibitor_eff = np.concatenate([
        np.full(25, 85.0),
        np.full(20, 50.0),
        np.full(15, 92.0)
    ])

    df = pd.DataFrame({
        "timestamp": timestamps,
        "temp_c": np.round(temp_c, 2),
        "pressure_bar": np.round(pressure_bar, 2),
        "ph": np.round(ph, 2),
        "h2s_ppm": np.round(np.clip(h2s, 5, 1000), 1),
        "co2_mol_pct": np.round(np.clip(co2, 0.2, 10.0), 2),
        "chlorides_ppm": np.round(np.clip(chlorides, 1000, 150000), 0),
        "water_cut_pct": np.round(np.clip(water_cut, 1, 95), 1),
        "inhibitor_eff_pct": np.round(inhibitor_eff, 1),
    })
    return df.to_csv(index=False).encode("utf-8")


# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
st.sidebar.title("🛢️ DRVT Pipeline Control")
mode = st.sidebar.radio(
    "Operational Mode",
    ["1. Interactive Chemo-Resonant Twin", "2. Field Telemetry CSV Analyzer"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Preset Operating Scenarios")
preset = st.sidebar.selectbox(
    "Load Field Scenario",
    [
        "Custom Parameters",
        "Sweet Crude (Passivated Baseline)",
        "Sour Gas Excursion (High H2S & Low pH)",
        "High-Salinity Water Cut (Chloride Pitting)",
        "Hot Mature Field (FeS / CaCO3 Scale Fouling)"
    ]
)

defaults = {
    "f0": 5.80, "q0": 1800, "wall": 14.2, "grade": "API 5L X65 (High-Strength CS)",
    "temp": 48.0, "press": 65.0, "ph": 6.5, "h2s": 40.0, "co2": 1.2,
    "cl": 22000.0, "wc": 18.0, "inh": 85.0, "months": 12.0, "length_km": 10.0
}

if preset == "Sweet Crude (Passivated Baseline)":
    defaults.update({"temp": 42.0, "press": 55.0, "ph": 6.8, "h2s": 15.0, "co2": 0.8, "cl": 12000.0, "wc": 12.0, "inh": 90.0, "months": 12.0})
elif preset == "Sour Gas Excursion (High H2S & Low pH)":
    defaults.update({"temp": 62.0, "press": 82.0, "ph": 5.1, "h2s": 480.0, "co2": 3.6, "cl": 38000.0, "wc": 42.0, "inh": 45.0, "months": 18.0})
elif preset == "High-Salinity Water Cut (Chloride Pitting)":
    defaults.update({"temp": 55.0, "press": 70.0, "ph": 5.9, "h2s": 85.0, "co2": 2.1, "cl": 95000.0, "wc": 65.0, "inh": 60.0, "months": 24.0})
elif preset == "Hot Mature Field (FeS / CaCO3 Scale Fouling)":
    defaults.update({"temp": 88.0, "press": 60.0, "ph": 7.6, "h2s": 310.0, "co2": 1.5, "cl": 45000.0, "wc": 52.0, "inh": 70.0, "months": 30.0})

st.sidebar.markdown("---")
st.sidebar.subheader("Pipe & DRVT Sensor Specs")
pipe_grade = st.sidebar.selectbox(
    "Pipeline Steel Grade",
    ["API 5L X52 (Carbon Steel)", "API 5L X65 (High-Strength CS)", "API 5L X70 (Sour Service)", "Duplex Stainless Steel 2205"],
    index=["API 5L X52 (Carbon Steel)", "API 5L X65 (High-Strength CS)", "API 5L X70 (Sour Service)", "Duplex Stainless Steel 2205"].index(defaults["grade"])
)
wall_thickness_mm = st.sidebar.slider("Nominal Wall Thickness (mm)", 6.0, 32.0, defaults["wall"], 0.2)
pipe_length_km = st.sidebar.slider("Monitored Pipeline Length (km)", 0.5, 100.0, defaults["length_km"], 0.5)
f0_ghz = st.sidebar.slider("Baseline Sensor Frequency f₀ (GHz)", 1.0, 24.0, defaults["f0"], 0.1)
q0 = st.sidebar.slider("Baseline Cavity Q-Factor (Q₀)", 500, 5000, defaults["q0"], 50)
exposure_months = st.sidebar.slider("Service Exposure Window (Months)", 1.0, 60.0, defaults["months"], 1.0)

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.markdown('<div class="main-header">🛢️ DRVT Oil & Gas Pipeline Integrity & Chemical Monitor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Chemo-Resonant Non-Destructive Testing (NDT) & Digital Twin coupling internal fluid electrochemistry (H₂S, CO₂, pH, Cl⁻) with Dynamic Resonant Volume Theory</div>',
    unsafe_allow_html=True
)

# =========================================================
# MODE 1: INTERACTIVE CHEMO-RESONANT DIGITAL TWIN
# =========================================================
if mode == "1. Interactive Chemo-Resonant Twin":
    st.subheader("1. Internal Fluid Chemistry & Operating Conditions")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        h2s_ppm = st.slider("H₂S Concentration (ppm)", 0.0, 1000.0, defaults["h2s"], 5.0)
        co2_mol_pct = st.slider("CO₂ Partial Content (mol%)", 0.0, 10.0, defaults["co2"], 0.1)
    with c2:
        ph = st.slider("Produced Water pH", 3.5, 8.5, defaults["ph"], 0.1)
        chlorides_ppm = st.slider("Chlorides / Salinity (ppm)", 500.0, 150000.0, defaults["cl"], 500.0)
    with c3:
        water_cut_pct = st.slider("Water Cut (%)", 0.0, 100.0, defaults["wc"], 1.0)
        inhibitor_eff_pct = st.slider("Corrosion Inhibitor Efficiency (%)", 0.0, 100.0, defaults["inh"], 1.0)
    with c4:
        temp_c = st.slider("Fluid Temperature (°C)", 15.0, 130.0, defaults["temp"], 1.0)
        pressure_bar = st.slider("Operating Pressure (bar)", 5.0, 180.0, defaults["press"], 1.0)

    res = compute_chemo_drvt_metrics(
        f0_ghz, q0, wall_thickness_mm, pipe_grade,
        temp_c, pressure_bar, ph, h2s_ppm, co2_mol_pct,
        chlorides_ppm, water_cut_pct, inhibitor_eff_pct, exposure_months
    )

    # 4-Stage Digital Twin Pipeline Flow
    st.markdown("---")
    st.subheader("2. Live 4-Stage Chemo-Resonant Digital Twin Flow")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""
        <div class="stage-box">
            <b>Stage 1: Nominal Pipe</b><br>
            Wall: {wall_thickness_mm:.1f} mm | f₀: {f0_ghz:.2f} GHz<br>
            Q₀: {q0} | {pipe_grade.split()[2]}
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
        <div class="stage-box">
            <b>Stage 2: Fluid Electrochemistry</b><br>
            H₂S: {h2s_ppm:.0f} ppm | CO₂: {co2_mol_pct:.1f}%<br>
            pH: {ph:.1f} | Water Cut: {water_cut_pct:.0f}%
        </div>
        """, unsafe_allow_html=True)
    with s3:
        st.markdown(f"""
        <div class="stage-box">
            <b>Stage 3: DRVT Cavity Shift</b><br>
            ROD Shift: +{res['rod_shift_pct']:.2f}%<br>
            ΔV_eff: {res['dv_rel_pct']:+.2f}% | Q: {res['q_loaded']:.0f}
        </div>
        """, unsafe_allow_html=True)
    with s4:
        st.markdown(f"""
        <div class="stage-box" style="border-bottom-color: {'#16A34A' if res['scii']>=80 else ('#F59E0B' if res['scii']>=55 else '#DC2626')};">
            <b>Stage 4: Integrity Diagnosis</b><br>
            SCII Score: {res['scii']:.1f} / 100<br>
            {res['status']}
        </div>
        """, unsafe_allow_html=True)

    # Key Performance Metrics
    st.markdown("---")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Integrity Index (SCII)", f"{res['scii']:.1f} / 100", f"{res['scii']-100:.1f}")
    m2.metric("Corrosion Rate", f"{res['corrosion_rate_mmy']:.2f} mm/yr", "Target < 0.15", delta_color="inverse")
    m3.metric("Remaining Wall", f"{res['remaining_wall_mm']:.2f} mm", f"-{res['wall_loss_mm']:.2f} mm ({res['wall_loss_pct']:.1f}%)", delta_color="inverse")
    m4.metric("ROD Shift", f"{res['rod_shift_pct']:.2f} %", f"Δf = {(res['f_resonant_ghz']-f0_ghz)*1000:+.1f} MHz")
    m5.metric("Scale / FeS Index", f"{res['scale_index']:.2f}", f"Loaded Q = {res['q_loaded']:.0f}")

    # Visual Diagnostics
    st.markdown("---")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        freq_span = np.linspace(f0_ghz * 0.96, f0_ghz * 1.04, 500)
        s11_nominal = -22.0 / (1.0 + (2.0 * q0 * (freq_span - f0_ghz) / f0_ghz) ** 2)
        s11_degraded = -(22.0 * (res["q_loaded"] / q0)) / (
            1.0 + (2.0 * res["q_loaded"] * (freq_span - res["f_resonant_ghz"]) / res["f_resonant_ghz"]) ** 2
        )

        fig_spec = go.Figure()
        fig_spec.add_trace(go.Scatter(x=freq_span, y=s11_nominal, name="Pristine Pipe Baseline (S11)", line=dict(color="#0284C7", width=2.5, dash="dash")))
        fig_spec.add_trace(go.Scatter(x=freq_span, y=s11_degraded, name="Current Chemo-Resonant State", line=dict(color="#DC2626", width=3)))
        fig_spec.update_layout(
            title="DRVT Microwave Cavity Reflection Spectrum (S11)",
            xaxis_title="Frequency (GHz)",
            yaxis_title="Return Loss S11 (dB)",
            height=370,
            margin=dict(l=20, r=20, t=45, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_spec, use_container_width=True)

    with col_chart2:
        months_proj = np.linspace(0, 60, 61)
        wall_proj = np.maximum(0.0, wall_thickness_mm - res["corrosion_rate_mmy"] * (months_proj / 12.0))
        min_allowable = wall_thickness_mm * 0.75

        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(x=months_proj, y=wall_proj, name="Projected Wall Thickness (mm)", line=dict(color="#0F172A", width=3)))
        fig_proj.add_hline(y=min_allowable, line_dash="dot", line_color="#DC2626", annotation_text="API Minimum Allowable Wall (75%)")
        fig_proj.add_vline(x=exposure_months, line_dash="dash", line_color="#0284C7", annotation_text="Current Exposure")
        fig_proj.update_layout(
            title="5-Year Wall Thinning Trajectory under Current Chemistry",
            xaxis_title="Exposure Time (Months)",
            yaxis_title="Wall Thickness (mm)",
            height=370,
            margin=dict(l=20, r=20, t=45, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_proj, use_container_width=True)

    # Automated Engineering & Chemical Recommendations
    st.markdown("---")
    st.subheader("3. Automated Chemical & NDT Decision Support")
    st.info(f"**Dominant Degradation Mechanism:** {res['dominant_mechanism']} | **Thermal Drift Compensated:** {res['thermal_shift_mhz']:+.2f} MHz")

    chem_recs, mech_recs = generate_recommendations(res, h2s_ppm, co2_mol_pct, ph, inhibitor_eff_pct, res["scale_index"])
    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown("#### 🧪 Chemical Dosing & Process Actions")
        for item in chem_recs:
            st.markdown(f"- {item}")
    with rc2:
        st.markdown("#### 🔧 Mechanical & NDT Inspection Actions")
        for item in mech_recs:
            st.markdown(f"- {item}")

    # Inspection Point Spacing & Sampling Interval Planner
    st.markdown("---")
    st.subheader("4. Inspection Point Spacing & Sampling Interval Planner")
    plan = build_inspection_plan(res, h2s_ppm, co2_mol_pct, ph, water_cut_pct, pipe_length_km)

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Inspection Risk Tier", plan["risk_tier"].split(" (")[0])
    p2.metric("Critical Point Spacing", f"{plan['critical_spacing_m']} m", "Bends / Sag / Welds")
    p3.metric("Straight Run Spacing", f"{plan['straight_spacing_m']} m", f"~{plan['estimated_straight_points']} nodes")
    p4.metric("Sampling / Polling Rate", plan["polling_interval"].split(" (")[0], plan["polling_interval"])

    st.dataframe(plan["schedule_df"], use_container_width=True)
    st.download_button(
        label="📥 Download Inspection Point Schedule (CSV)",
        data=plan["schedule_df"].to_csv(index=False).encode("utf-8"),
        file_name="drvt_pipeline_inspection_schedule.csv",
        mime="text/csv"
    )

# =========================================================
# MODE 2: FIELD TELEMETRY CSV ANALYZER
# =========================================================
else:
    st.subheader("Field Chemo-Resonant Telemetry CSV Analyzer")
    st.markdown(
        "Upload time-series SCADA / laboratory fluid chemistry and sensor telemetry (`CSV`) to track **ROD Shift**, isolate thermal drift from chemical wall thinning, and detect sour gas or pitting excursions."
    )

    col_dl, col_up = st.columns([1, 2])
    with col_dl:
        st.download_button(
            label="📥 Download Sample Pipeline CSV",
            data=generate_sample_csv(),
            file_name="drvt_pipeline_telemetry_sample.csv",
            mime="text/csv"
        )
    with col_up:
        uploaded_file = st.file_uploader("Upload Pipeline Telemetry CSV", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        st.caption("Showing built-in sample telemetry dataset (60 time steps including a simulated sour gas excursion & chemical batch recovery).")
        df = pd.read_csv(io.BytesIO(generate_sample_csv()))

    required_cols = {"temp_c", "pressure_bar", "ph", "h2s_ppm", "co2_mol_pct", "chlorides_ppm", "water_cut_pct"}
    if not required_cols.issubset(set(df.columns)):
        st.error(f"CSV is missing required columns: {required_cols - set(df.columns)}")
    else:
        if "inhibitor_eff_pct" not in df.columns:
            df["inhibitor_eff_pct"] = 80.0
        if "timestamp" not in df.columns:
            df["timestamp"] = np.arange(len(df))

        dt_years = 6.0 / (24.0 * 365.0)
        cum_loss = 0.0
        scii_list, rod_list, rate_list, wall_list, status_list = [], [], [], [], []

        for _, row in df.iterrows():
            step_res = compute_chemo_drvt_metrics(
                f0_ghz=f0_ghz, q0=q0, wall_thickness_mm=wall_thickness_mm, pipe_grade=pipe_grade,
                temp_c=float(row["temp_c"]), pressure_bar=float(row["pressure_bar"]),
                ph=float(row["ph"]), h2s_ppm=float(row["h2s_ppm"]),
                co2_mol_pct=float(row["co2_mol_pct"]), chlorides_ppm=float(row["chlorides_ppm"]),
                water_cut_pct=float(row["water_cut_pct"]), inhibitor_eff_pct=float(row["inhibitor_eff_pct"]),
                exposure_months=12.0
            )
            cum_loss += step_res["corrosion_rate_mmy"] * dt_years
            rem_wall = max(0.5, wall_thickness_mm - cum_loss)
            adj_scii = np.clip(step_res["scii"] - (cum_loss / wall_thickness_mm) * 120.0, 0.0, 100.0)

            scii_list.append(round(adj_scii, 2))
            rod_list.append(round(step_res["rod_shift_pct"], 2))
            rate_list.append(round(step_res["corrosion_rate_mmy"], 3))
            wall_list.append(round(rem_wall, 3))
            status_list.append(step_res["status"])

        df["SCII_Score"] = scii_list
        df["ROD_Shift_Pct"] = rod_list
        df["Corrosion_Rate_mmy"] = rate_list
        df["Remaining_Wall_mm"] = wall_list
        df["Diagnosis"] = status_list

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Minimum SCII Recorded", f"{df['SCII_Score'].min():.1f} / 100")
        k2.metric("Peak Corrosion Rate", f"{df['Corrosion_Rate_mmy'].max():.2f} mm/yr")
        k3.metric("Peak ROD Shift", f"{df['ROD_Shift_Pct'].max():.2f} %")
        k4.metric("Final Remaining Wall", f"{df['Remaining_Wall_mm'].iloc[-1]:.3f} mm")

        fig_ts = make_subplots(
            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.10,
            subplot_titles=("Structural & Chemical Integrity Index (SCII) & ROD Shift (%)", "Fluid Chemistry Drivers: H₂S (ppm) & Produced Water pH")
        )
        fig_ts.add_trace(go.Scatter(x=df["timestamp"], y=df["SCII_Score"], name="SCII Score (0-100)", line=dict(color="#0F172A", width=2.5)), row=1, col=1)
        fig_ts.add_trace(go.Scatter(x=df["timestamp"], y=df["ROD_Shift_Pct"], name="ROD Shift (%)", line=dict(color="#DC2626", width=2, dash="dot")), row=1, col=1)

        fig_ts.add_trace(go.Scatter(x=df["timestamp"], y=df["h2s_ppm"], name="H₂S (ppm)", line=dict(color="#D97706", width=2)), row=2, col=1)
        fig_ts.add_trace(go.Scatter(x=df["timestamp"], y=df["ph"] * 50.0, name="pH (scaled ×50)", line=dict(color="#0284C7", width=2)), row=2, col=1)

        fig_ts.update_layout(height=540, margin=dict(l=20, r=20, t=50, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1))
        st.plotly_chart(fig_ts, use_container_width=True)

        st.subheader("Analyzed Telemetry Log")
        st.dataframe(df[["timestamp", "h2s_ppm", "co2_mol_pct", "ph", "water_cut_pct", "Corrosion_Rate_mmy", "ROD_Shift_Pct", "SCII_Score", "Diagnosis"]], use_container_width=True)
