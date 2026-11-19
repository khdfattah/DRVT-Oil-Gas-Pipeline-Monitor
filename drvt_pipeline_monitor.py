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
    page_title="DRVT Pipeline NDT Engine",
    page_icon="📡",
    layout="wide"
)

# ---------------------------------------------------------
# DRVT NDT Core Functions
# ---------------------------------------------------------
def compute_drvt_ndt_point(
    f0_ghz: float,
    q0: float,
    v_eff0_mm3: float,
    rod0: float,
    flaw_type: str,
    flaw_severity: float,
    coupling_gain: float = 1.0,
    noise_level: float = 0.02
):
    """
    Computes DRVT Non-Destructive Testing (NDT) observables for a pipeline section:
    - Effective Resonant Volume shift (dV_eff / V_eff0)
    - Resonant Occupation Density (ROD) and ROD Shift (%)
    - Shifted resonant frequency (f_res) and loaded quality factor (Q_eff)
    - NDT Defect Indication Index (NDII: 0 to 100)
    """
    s = float(np.clip(flaw_severity, 0.0, 1.0))

    profiles = {
        "Pristine Pipe Section":     (0.00, 0.00, 0.00, -1.0),
        "Wall Thinning (NDT Loss)":  (0.45, 1.30, 0.55, -1.0),
        "Internal Flaw / Crack":     (0.18, 1.65, 0.95, -1.0),
        "Inner Scale / Deposit":     (-0.28, 1.10, 0.75, +1.0),
        "Weld Zone Anomaly":         (0.12, 1.45, 0.85, -1.0),
    }
    dv_w, rod_w, q_w, freq_dir = profiles.get(flaw_type, (0.20, 1.20, 0.60, -1.0))

    dv_rel = freq_dir * dv_w * s * coupling_gain
    v_eff_mm3 = max(1e-6, v_eff0_mm3 * (1.0 + dv_rel))

    rod_shift_pct = (rod_w * s * 18.0 * coupling_gain) + (abs(dv_rel) * 35.0)
    rod_eff = rod0 * (1.0 + rod_shift_pct / 100.0)

    q_eff = max(10.0, q0 / (1.0 + q_w * s * 2.4 * coupling_gain))

    df_rel = -0.35 * dv_rel + np.random.normal(0.0, noise_level * 1e-3)
    f_res_ghz = f0_ghz * (1.0 + df_rel)

    ndii = float(np.clip(rod_shift_pct * 2.2 + (1.0 - q_eff / q0) * 45.0, 0.0, 100.0))

    if ndii < 15.0:
        indication = "NO SIGNIFICANT FLAW (Nominal DRVT Baseline)"
    elif ndii < 45.0:
        indication = "MINOR RESONANT ANOMALY (Monitor & Re-Scan)"
    elif ndii < 75.0:
        indication = "MODERATE NDT INDICATION (Targeted Local NDT)"
    else:
        indication = "STRONG NDT INDICATION (Immediate Verification Required)"

    return {
        "v_eff_mm3": v_eff_mm3,
        "dv_rel_pct": dv_rel * 100.0,
        "rod_eff": rod_eff,
        "rod_shift_pct": rod_shift_pct,
        "q_eff": q_eff,
        "f_res_ghz": f_res_ghz,
        "df_mhz": (f_res_ghz - f0_ghz) * 1000.0,
        "ndii": ndii,
        "indication": indication,
    }


def invert_measured_resonance(
    position_m: float,
    f_res_ghz: float,
    q_eff: float,
    f0_ghz: float,
    q0: float,
    v_eff0_mm3: float,
    rod0: float,
    coupling_gain: float = 1.0
):
    """
    Computes DRVT ROD Shift (%), dV_eff (%), V_eff, ROD_eff, and NDII
    from measured resonant frequency (f_res_ghz) and quality factor (q_eff).
    """
    gain = max(coupling_gain, 1e-6)
    f_res_safe = max(f_res_ghz, 1e-9)
    q_eff_safe = max(q_eff, 1e-6)

    # Relate fractional frequency shift to effective volume shift: df/f0 ~ -0.35 * (dV_eff / V_eff0)
    df_rel = (f_res_safe - f0_ghz) / f0_ghz
    dv_rel = float(np.clip(-df_rel / 0.35, -0.90, 2.50))
    v_eff_mm3 = max(1e-6, v_eff0_mm3 * (1.0 + dv_rel))

    # Quality factor loss fraction
    q_loss_frac = float(np.clip(1.0 - (q_eff_safe / max(q0, 1e-6)), 0.0, 0.99))

    # ROD Shift (%) combining resonant volume perturbation and Q-factor dissipation
    rod_shift_pct = float(np.clip((abs(dv_rel) * 120.0 + q_loss_frac * 45.0) * gain, 0.0, 500.0))
    rod_eff = rod0 * (1.0 + rod_shift_pct / 100.0)

    # NDT Defect Indication Index (0 to 100)
    ndii = float(np.clip(rod_shift_pct * 2.0 + q_loss_frac * 40.0, 0.0, 100.0))

    if ndii < 15.0:
        status = "Nominal"
    elif ndii < 45.0:
        status = "Minor Anomaly"
    elif ndii < 75.0:
        status = "Moderate Indication"
    else:
        status = "Strong Indication"

    return {
        "Position_m": round(float(position_m), 2),
        "f_res_ghz": round(float(f_res_safe), 5),
        "df_mhz": round(float((f_res_safe - f0_ghz) * 1000.0), 3),
        "Q_eff": round(float(q_eff_safe), 1),
        "dV_eff_Pct": round(dv_rel * 100.0, 2),
        "V_eff_mm3": round(v_eff_mm3, 1),
        "ROD_Shift_Pct": round(rod_shift_pct, 2),
        "ROD_eff": round(rod_eff, 3),
        "NDII": round(ndii, 1),
        "Status": status,
    }


def make_sample_ndt_csv(f0_ghz: float, q0: float) -> bytes:
    """Generates a sample NDT scan CSV with Position_m, f_res_ghz, and Q_eff."""
    positions = np.linspace(0.0, 50.0, 51)
    # Localized anomaly centered around 28 m
    bump = np.exp(-0.5 * ((positions - 28.0) / 3.5) ** 2)
    f_res = f0_ghz * (1.0 - 0.008 * bump)
    q_eff = q0 / (1.0 + 1.8 * bump)

    df = pd.DataFrame({
        "Position_m": np.round(positions, 2),
        "f_res_ghz": np.round(f_res, 5),
        "Q_eff": np.round(q_eff, 1),
    })
    return df.to_csv(index=False).encode("utf-8")


def simulate_ndt_scan(
    scan_length_m: float,
    num_points: int,
    f0_ghz: float,
    q0: float,
    v_eff0_mm3: float,
    rod0: float,
    flaw_type: str,
    peak_severity: float,
    coupling_gain: float,
    seed: int = 7
):
    """Simulates a 1D DRVT NDT inspection scan along a pipeline segment with a localized flaw."""
    rng = np.random.default_rng(seed)
    positions_m = np.linspace(0.0, scan_length_m, num_points)
    center_m = scan_length_m * 0.55
    width_m = max(scan_length_m * 0.08, 0.5)

    local_profile = np.exp(-0.5 * ((positions_m - center_m) / width_m) ** 2)
    severities = np.clip(peak_severity * local_profile + rng.normal(0.0, 0.015, num_points), 0.0, 1.0)

    rows = []
    for x_m, sev in zip(positions_m, severities):
        res = compute_drvt_ndt_point(
            f0_ghz=f0_ghz,
            q0=q0,
            v_eff0_mm3=v_eff0_mm3,
            rod0=rod0,
            flaw_type=flaw_type,
            flaw_severity=float(sev),
            coupling_gain=coupling_gain,
            noise_level=0.01
        )
        rows.append({
            "Position_m": round(float(x_m), 2),
            "Local_Severity": round(float(sev), 3),
            "ROD_Shift_Pct": round(res["rod_shift_pct"], 2),
            "dV_eff_Pct": round(res["dv_rel_pct"], 2),
            "Q_eff": round(res["q_eff"], 1),
            "NDII": round(res["ndii"], 1),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------
# Sidebar: DRVT Probe & Pipeline Reference Parameters
# ---------------------------------------------------------
st.sidebar.title("📡 DRVT NDT Probe Setup")
f0_ghz = st.sidebar.slider("Reference Resonant Frequency f₀ (GHz)", 1.0, 30.0, 6.0, 0.5)
q0 = st.sidebar.slider("Baseline Quality Factor Q₀", 200, 5000, 1500, 50)
v_eff0_mm3 = st.sidebar.number_input("Baseline Effective Volume V_eff,0 (mm³)", min_value=1.0, max_value=100000.0, value=1250.0, step=50.0)
rod0 = st.sidebar.slider("Baseline ROD₀", 0.1, 10.0, 1.0, 0.1)
coupling_gain = st.sidebar.slider("DRVT Mode-Coupling Sensitivity", 0.2, 2.5, 1.0, 0.1)

# ---------------------------------------------------------
# Main Workspace
# ---------------------------------------------------------
st.title("📡 DRVT Non-Destructive Testing (NDT) for Oil & Gas Pipelines")
st.caption("Resonant volume perturbation, ROD shift, and quality-factor tracking for pipeline NDT defect detection.")

tab_spot, tab_scan, tab_csv = st.tabs([
    "Spot NDT Resonance Analysis",
    "Along-Pipe NDT Scan Profile",
    "Upload NDT Scan CSV"
])

# =========================================================
# TAB 1: SPOT NDT RESONANCE ANALYSIS
# =========================================================
with tab_spot:
    c1, c2 = st.columns(2)
    with c1:
        flaw_type = st.selectbox(
            "NDT Target / Flaw Mode",
            [
                "Pristine Pipe Section",
                "Wall Thinning (NDT Loss)",
                "Internal Flaw / Crack",
                "Inner Scale / Deposit",
                "Weld Zone Anomaly"
            ]
        )
    with c2:
        flaw_severity = st.slider("Perturbation Severity", 0.0, 1.0, 0.45, 0.01)

    res = compute_drvt_ndt_point(
        f0_ghz=f0_ghz,
        q0=q0,
        v_eff0_mm3=v_eff0_mm3,
        rod0=rod0,
        flaw_type=flaw_type,
        flaw_severity=flaw_severity,
        coupling_gain=coupling_gain,
        noise_level=0.0
    )

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("ROD Shift", f"+{res['rod_shift_pct']:.2f} %", f"ROD_eff: {res['rod_eff']:.3f}")
    m2.metric("Effective Volume V_eff", f"{res['v_eff_mm3']:.1f} mm³", f"ΔV_eff: {res['dv_rel_pct']:+.2f}%")
    m3.metric("Effective Q-Factor", f"{res['q_eff']:.0f}", f"Baseline Q₀: {q0}")
    m4.metric("NDT Indication (NDII)", f"{res['ndii']:.1f} / 100", f"Δf: {res['df_mhz']:+.2f} MHz")

    st.info(f"**DRVT NDT Assessment:** {res['indication']}")

    f_axis = np.linspace(f0_ghz * 0.94, f0_ghz * 1.06, 400)
    resp_base = 1.0 / (1.0 + (2.0 * q0 * (f_axis - f0_ghz) / f0_ghz) ** 2)
    resp_ndt = (res["q_eff"] / q0) / (1.0 + (2.0 * res["q_eff"] * (f_axis - res["f_res_ghz"]) / res["f_res_ghz"]) ** 2)

    fig_r = go.Figure()
    fig_r.add_trace(go.Scatter(x=f_axis, y=resp_base, name="Nominal Pipe Resonance", line=dict(color="#0284C7", width=2.5, dash="dash")))
    fig_r.add_trace(go.Scatter(x=f_axis, y=resp_ndt, name="NDT Perturbed Resonance", line=dict(color="#DC2626", width=3)))
    fig_r.update_layout(
        title="DRVT Resonant Mode Profile (Frequency Shift & Q Broadening)",
        xaxis_title="Frequency (GHz)",
        yaxis_title="Normalized Resonant Response",
        height=360,
        margin=dict(l=20, r=20, t=45, b=20)
    )
    st.plotly_chart(fig_r, use_container_width=True)

# =========================================================
# TAB 2: ALONG-PIPE NDT SCAN PROFILE
# =========================================================
with tab_scan:
    s1, s2, s3 = st.columns(3)
    with s1:
        scan_flaw = st.selectbox(
            "Scan Flaw Signature",
            [
                "Wall Thinning (NDT Loss)",
                "Internal Flaw / Crack",
                "Inner Scale / Deposit",
                "Weld Zone Anomaly"
            ],
            key="scan_flaw_select"
        )
    with s2:
        scan_length_m = st.slider("Inspection Segment Length (m)", 5.0, 200.0, 40.0, 5.0)
    with s3:
        peak_sev = st.slider("Peak Flaw Severity", 0.1, 1.0, 0.75, 0.05)

    scan_df = simulate_ndt_scan(
        scan_length_m=scan_length_m,
        num_points=120,
        f0_ghz=f0_ghz,
        q0=q0,
        v_eff0_mm3=v_eff0_mm3,
        rod0=rod0,
        flaw_type=scan_flaw,
        peak_severity=peak_sev,
        coupling_gain=coupling_gain
    )

    fig_s = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
        subplot_titles=("DRVT ROD Shift (%) & NDT Indication Index (NDII)", "Effective Quality Factor (Q_eff) Along Pipe")
    )
    fig_s.add_trace(go.Scatter(x=scan_df["Position_m"], y=scan_df["ROD_Shift_Pct"], name="ROD Shift (%)", line=dict(color="#DC2626", width=2.5)), row=1, col=1)
    fig_s.add_trace(go.Scatter(x=scan_df["Position_m"], y=scan_df["NDII"], name="NDII (0-100)", line=dict(color="#0F172A", width=2, dash="dot")), row=1, col=1)
    fig_s.add_trace(go.Scatter(x=scan_df["Position_m"], y=scan_df["Q_eff"], name="Q_eff", line=dict(color="#0284C7", width=2.5)), row=2, col=1)
    fig_s.update_xaxes(title_text="Pipeline Axial Position (m)", row=2, col=1)
    fig_s.update_layout(height=480, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_s, use_container_width=True)

    st.dataframe(scan_df, use_container_width=True, hide_index=True)

# =========================================================
# TAB 3: UPLOAD NDT SCAN CSV
# =========================================================
with tab_csv:
    st.subheader("Measured Pipe Scan CSV Processor")
    st.caption("Required columns: Position_m, f_res_ghz, Q_eff")

    col_dl, col_up = st.columns([1, 2])
    with col_dl:
        st.download_button(
            label="📥 Download Sample NDT Scan CSV",
            data=make_sample_ndt_csv(f0_ghz=f0_ghz, q0=q0),
            file_name="sample_drvt_ndt_scan.csv",
            mime="text/csv"
        )
    with col_up:
        uploaded_scan = st.file_uploader("Upload Pipeline NDT Scan CSV", type=["csv"])

    raw_df = pd.read_csv(uploaded_scan) if uploaded_scan is not None else pd.read_csv(io.BytesIO(make_sample_ndt_csv(f0_ghz=f0_ghz, q0=q0)))
    req_cols = {"Position_m", "f_res_ghz", "Q_eff"}

    if not req_cols.issubset(set(raw_df.columns)):
        st.error(f"Missing required columns: {sorted(list(req_cols - set(raw_df.columns)))}")
    else:
        processed_rows = [
            invert_measured_resonance(
                position_m=float(row["Position_m"]),
                f_res_ghz=float(row["f_res_ghz"]),
                q_eff=float(row["Q_eff"]),
                f0_ghz=f0_ghz,
                q0=q0,
                v_eff0_mm3=v_eff0_mm3,
                rod0=rod0,
                coupling_gain=coupling_gain
            )
            for _, row in raw_df.iterrows()
        ]
        out_df = pd.DataFrame(processed_rows)

        k1, k2, k3 = st.columns(3)
        k1.metric("Peak ROD Shift", f"+{out_df['ROD_Shift_Pct'].max():.2f} %")
        k2.metric("Peak NDII", f"{out_df['NDII'].max():.1f} / 100")
        max_row = out_df.loc[out_df["NDII"].idxmax()]
        k3.metric("Max Indication Position", f"{max_row['Position_m']:.2f} m", f"NDII: {max_row['NDII']:.1f}")

        fig_u = make_subplots(
            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
            subplot_titles=("Computed ROD Shift (%) & NDII Along Measured Points", "Computed Effective Volume Shift dV_eff (%)")
        )
        fig_u.add_trace(go.Scatter(x=out_df["Position_m"], y=out_df["ROD_Shift_Pct"], name="ROD Shift (%)", line=dict(color="#DC2626", width=2.5)), row=1, col=1)
        fig_u.add_trace(go.Scatter(x=out_df["Position_m"], y=out_df["NDII"], name="NDII", line=dict(color="#0F172A", width=2, dash="dot")), row=1, col=1)
        fig_u.add_trace(go.Scatter(x=out_df["Position_m"], y=out_df["dV_eff_Pct"], name="dV_eff (%)", line=dict(color="#0284C7", width=2.5)), row=2, col=1)
        fig_u.update_xaxes(title_text="Position_m (m)", row=2, col=1)
        fig_u.update_layout(height=480, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_u, use_container_width=True)

        st.dataframe(out_df, use_container_width=True, hide_index=True)
        st.download_button(
            label="📥 Download Computed DRVT NDT Results CSV",
            data=out_df.to_csv(index=False).encode("utf-8"),
            file_name="drvt_ndt_computed_results.csv",
            mime="text/csv"
        )
