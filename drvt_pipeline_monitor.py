import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    from fpdf import FPDF
    HAS_FPDF = True
except Exception:
    FPDF = None
    HAS_FPDF = False

st.set_page_config(page_title="DRVT Oil & Gas Pipeline Monitor", layout="wide")

lang = st.sidebar.radio("🌐 Language / اللغة", ("English", "العربية"), horizontal=True)
is_ar = (lang == "العربية")

if is_ar:
    st.markdown(
        "<style>.main, .stSidebar { direction: rtl; text-align: right; } h1, h2, h3, p, div, label { text-align: right; }</style>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<style>.main, .stSidebar { direction: ltr; text-align: left; } h1, h2, h3, p, div, label { text-align: left; }</style>",
        unsafe_allow_html=True,
    )

st.title("🔬 DRVT Oil & Gas Pipeline Monitor")

if is_ar:
    st.info("**إعداد وتطوير:** د. خالد عبدالفتاح محمد عثمان | معهد مروي التكنولوجي، جامعة مروي التكنولوجية، السودان (`khdfattah@gmail.com`)")
    ndt_opts = ("الموجات الموجهة (GWT)", "الموجات فوق الصوتية (UT)", "الميكروويف الداخلي (EM)")
    ndt_choice = st.sidebar.selectbox("🔍 نوع الجهاز اللاتلافي (NDT):", ndt_opts)
    defect_pct = st.sidebar.slider("نسبة التآكل / الترسبات المستهدفة (%)", 0, 50, 15)
    show_resonant = st.sidebar.checkbox("🔬 إظهار القراءات الرنينية (للبحث)", value=False)
    exp_label = "⚙️ مدخلات الأنبوب والجهاز (حدود واقعية مباشرة)"
else:
    st.info("**Author:** Dr. Khalid Abdel Fattah Mohamed Osman | Merowe Institute of Technology, Merowe University of Technology, Sudan")
    ndt_opts = ("Guided Wave Testing (GWT)", "Ultrasonic Thickness (UT)", "Internal Microwave (EM)")
    ndt_choice = st.sidebar.selectbox("🔍 NDT Device Type:", ndt_opts)
    defect_pct = st.sidebar.slider("Target Corrosion / Scaling (%)", 0, 50, 15)
    show_resonant = st.sidebar.checkbox("🔬 Show DRVT Resonant Metrics (Research)", value=False)
    exp_label = "⚙️ Pipeline & Device Inputs (Direct Realistic Bounds)"

opt_gwt = (ndt_choice == ndt_opts[0])
opt_ut = (ndt_choice == ndt_opts[1])
opt_em = (ndt_choice == ndt_opts[2])

with st.sidebar.expander(exp_label, expanded=True):
    D_out_inch = st.number_input("D_out (in) / القطر الخارجي [2–48 in]", 2.0, 48.0, 12.75, 0.25)
    t_nom_mm = st.number_input("t_nom (mm) / السُمك الاسمي [3–40 mm]", 3.0, 40.0, 12.70, 0.10)
    L_m = st.number_input("L (m) / طول المقطع [1–100 m]", 1.0, 100.0, 10.0, 1.0)
    dp_mm = st.number_input("d_p (mm) / قطر مجس UT [5–50 mm]", 5.0, 50.0, 15.0, 1.0) if opt_ut else 15.0
    P_watt = st.number_input("P (W) / قدرة الإرسال [0.005–10 W]", 0.005, 10.0, 0.05, 0.01, format="%.3f")
    Q_base = st.number_input("Q₀ / معامل الجودة الأساسي [100–5000]", 100.0, 5000.0, 1000.0, 50.0)
    f_gwt_khz = st.number_input("f_GWT (kHz) [20–100 kHz]", 20.0, 100.0, 50.0, 1.0) if opt_gwt else 50.0
    f_ut_mhz = st.number_input("f_UT (MHz) [1–15 MHz]", 1.0, 15.0, 5.0, 0.5) if opt_ut else 5.0
    f_em_ghz = st.number_input("f_EM (GHz) [0.9–10 GHz]", 0.9, 10.0, 2.4, 0.1) if opt_em else 2.4
    Pg_bar = st.number_input("Pg (bar) / ضغط الغاز [5–150 bar]", 5.0, 150.0, 50.0, 5.0) if opt_em else 50.0
    eps_r = st.number_input("εr / ثابت العزل [1.0001–2.50]", 1.0001, 2.50, 1.0006, 0.001, format="%.4f") if opt_em else 1.0006

V_eq_m3 = 286.398e-27
h_const = 6.6261e-34
c_const = 299792458.0
vs_steel = 5900.0
denom_const = 2.0 * np.pi * h_const * (c_const ** 2)

D_out = D_out_inch * 0.0254
t_nom = t_nom_mm / 1000.0
D_in = max(D_out - 2.0 * t_nom, 1e-4)
dp_m = dp_mm / 1000.0
Pg_pa = Pg_bar * 100000.0

lam_gwt = vs_steel / (f_gwt_khz * 1000.0)
lam_ut = vs_steel / (f_ut_mhz * 1e6)
lam_em = c_const / ((f_em_ghz * 1e9) * np.sqrt(eps_r))


def get_step_data(pct):
    r = pct / 100.0
    q = Q_base * (1.0 - 0.5 * r)
    t_c = t_nom * (1.0 - r)
    loss_m = t_nom - t_c
    d_in_c = max(D_out - 2.0 * t_c, 1e-4)
    d_eff_c = max(D_in * (1.0 - r), 1e-4)
    scale_side_m = max((D_in - d_eff_c) / 2.0, 0.0)
    pg_c = Pg_pa * (1.0 + 0.36 * r)

    nres_g = ((np.pi / 4.0) * L_m * (D_out ** 2 - d_in_c ** 2)) / V_eq_m3
    rod_g = ((P_watt * q * (lam_gwt ** 2)) / denom_const) / nres_g

    nres_u = ((np.pi / 4.0) * (dp_m ** 2) * t_c) / V_eq_m3
    rod_u = ((P_watt * q * (lam_ut ** 2)) / denom_const) / nres_u

    nres_e = ((np.pi / 4.0) * (d_eff_c ** 2) * L_m) / V_eq_m3
    rod_e = ((P_watt * q * (lam_em ** 2)) / denom_const) / nres_e
    gdi = 14369.0 / pg_c
    c_idx = rod_e / gdi

    return q, t_c, loss_m, d_eff_c, scale_side_m, pg_c, nres_g, rod_g, nres_u, rod_u, rod_e, gdi, c_idx


def get_decision_info(pct):
    if pct < 10:
        status = "حالة سليمة / مستقرة" if is_ar else "Healthy / Stable Condition"
        status_en = "Healthy / Stable Condition"
        action = (
            "استمرار المراقبة الدورية المجدولة دون تدخل طارئ."
            if is_ar
            else "Continue scheduled routine monitoring with no urgent intervention."
        )
        action_en = "Continue scheduled routine monitoring with no urgent intervention."
        level = "ok"
    elif pct < 25:
        status = "تنبيه مبكر (ترقق أو ترسبات)" if is_ar else "Early Warning (Thinning / Scaling)"
        status_en = "Early Warning (Thinning / Scaling)"
        action = (
            "إجراء فحص موضعي تأكيدي ومراجعة معدل التآكل أو الترسبات وضغط التشغيل."
            if is_ar
            else "Perform confirmatory localized inspection and review corrosion/scaling rate and pressure."
        )
        action_en = "Perform confirmatory localized inspection and review corrosion/scaling rate and pressure."
        level = "warn"
    else:
        status = "حالة حرجة (تدخل هندسي عاجل)" if is_ar else "Critical Condition (Urgent Action)"
        status_en = "Critical Condition (Urgent Action)"
        action = (
            "رفع تنبيه تشغيلي عاجل وتقييم السلامة الإنشائية أو خفض الضغط وعزل المقطع."
            if is_ar
            else "Raise urgent integrity alert and evaluate structural safety, derating, or isolation."
        )
        action_en = "Raise urgent integrity alert and evaluate structural safety, derating, or isolation."
        level = "crit"
    return status, status_en, action, action_en, level


_, _, _, _, _, _, _, rod_g0, _, rod_u0, _, _, c_idx0 = get_step_data(0)
q_now, t_now, loss_now, d_eff_now, scale_side_now, pg_now, nres_g_now, rod_g_now, nres_u_now, rod_u_now, rod_e_now, gdi_now, c_idx_now = get_step_data(defect_pct)

diff_g = ((rod_g_now - rod_g0) / rod_g0) * 100.0
diff_u = ((rod_u_now - rod_u0) / rod_u0) * 100.0
diff_c = ((c_idx_now - c_idx0) / c_idx0) * 100.0
st_txt, st_en, act_txt, act_en, lvl_txt = get_decision_info(defect_pct)


def build_pdf_bytes():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    epw = max(pdf.w - pdf.l_margin - pdf.r_margin, 50.0)

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(epw, 10, "DRVT Pipeline Integrity Technical Report")

    pdf.set_font("Helvetica", size=10)
    method_ascii = "GWT" if opt_gwt else ("UT" if opt_ut else "EM")
    lines = [
        "Author: Dr. Khalid Abdel Fattah Mohamed Osman | Merowe University of Technology, Sudan",
        f"Method: {method_ascii}",
        f"Dimensions: OD={D_out_inch:.2f} in, t_nom={t_nom_mm:.2f} mm, L={L_m:.1f} m",
        f"Defect Ratio: {defect_pct}%",
        f"Status: {st_en}",
        f"Remaining Wall: {t_now * 1000:.2f} mm | Wall Loss: {loss_now * 1000:.2f} mm",
        f"Effective ID: {d_eff_now * 1000:.1f} mm | Scale/side: {scale_side_now * 1000:.1f} mm | Pg: {pg_now / 1e5:.1f} bar",
        f"Action: {act_en}",
    ]
    if show_resonant:
        lines.append(
            f"Resonant (Research): ROD_GWT={rod_g_now:.4e} ({diff_g:+.2f}%), "
            f"ROD_UT={rod_u_now:.4e} ({diff_u:+.2f}%), C_index={c_idx_now:.4e} ({diff_c:+.2f}%)"
        )
    for line in lines:
        safe = str(line).encode("latin-1", errors="replace").decode("latin-1")
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(epw, 7, safe)

    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")


tab1, tab2, tab3 = st.tabs(
    ("📊 النتائج والقرارات", "📈 الرسم البياني", "📄 التقرير الفني")
    if is_ar
    else ("📊 Results & Decisions", "📈 Chart", "📄 Technical Report")
)

with tab1:
    if lvl_txt == "ok":
        st.success(f"**{st_txt}** — {act_txt}")
    elif lvl_txt == "warn":
        st.warning(f"**{st_txt}** — {act_txt}")
    else:
        st.error(f"**{st_txt}** — {act_txt}")

    c1, c2, c3 = st.columns(3)
    if opt_gwt or opt_ut:
        c1.metric("السُمك المتبقي / Remaining t" if is_ar else "Remaining Thickness", f"{t_now*1000:.2f} mm", f"-{loss_now*1000:.2f} mm")
        c2.metric("الفقد في الجدار / Wall Loss" if is_ar else "Wall Loss", f"{loss_now*1000:.2f} mm", f"{defect_pct}%")
        c3.metric("معامل الجودة / Q Factor" if is_ar else "Quality Factor (Q)", f"{q_now:.0f}")
    else:
        c1.metric("القطر الداخلي الفعلي / Effective ID" if is_ar else "Effective ID", f"{d_eff_now*1000:.1f} mm", f"{scale_side_now*1000:.1f} mm/side")
        c2.metric("سُمك الترسبات / Scale/Side" if is_ar else "Scale / Side", f"{scale_side_now*1000:.1f} mm", f"{defect_pct}%")
        c3.metric("ضغط الغاز / Gas Pressure" if is_ar else "Gas Pressure", f"{pg_now/1e5:.1f} bar")

    if show_resonant:
        r1, r2, r3 = st.columns(3)
        if opt_gwt:
            r1.metric("ROD - GWT", f"{rod_g_now:.4e}", f"{diff_g:+.2f}%")
            r2.metric("N_res", f"{nres_g_now:.3e}")
            r3.metric("λ_GWT", f"{lam_gwt:.3f} m")
        elif opt_ut:
            r1.metric("ROD - UT", f"{rod_u_now:.4e}", f"{diff_u:+.2f}%")
            r2.metric("N_res", f"{nres_u_now:.3e}")
            r3.metric("λ_UT", f"{lam_ut*1000:.2f} mm")
        else:
            r1.metric("C_index - EM", f"{c_idx_now:.4e}", f"{diff_c:+.2f}%")
            r2.metric("ROD_EM", f"{rod_e_now:.4e}")
            r3.metric("GDI", f"{gdi_now:.3e}")

    st.divider()
    rows = []
    for s in (0, 5, 10, 15, 20, 25, 30, 40):
        qs, tc, lossm, dec, scalem, pgc, ng, rg, nu, ru, re, gdis, ci = get_step_data(s)
        sts, _, _, _, _ = get_decision_info(s)
        if opt_gwt or opt_ut:
            row = {"Defect (%)": f"{s}%", "t_rem (mm)": round(tc*1000, 2), "Loss (mm)": round(lossm*1000, 2), "Q": round(qs, 0), "Decision": sts}
            if show_resonant:
                val_r = rg if opt_gwt else ru
                val_0 = rod_g0 if opt_gwt else rod_u0
                row["ROD"] = f"{val_r:.4e}"
                row["Shift (%)"] = f"{((val_r - val_0) / val_0) * 100.0:+.2f}%"
            rows.append(row)
        else:
            row = {"Defect (%)": f"{s}%", "ID_eff (mm)": round(dec*1000, 1), "Scale/side (mm)": round(scalem*1000, 1), "Pg (bar)": round(pgc/1e5, 1), "Decision": sts}
            if show_resonant:
                row["C_index"] = f"{ci:.4e}"
                row["Shift (%)"] = f"{((ci - c_idx0) / c_idx0) * 100.0:+.2f}%"
            rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

with tab2:
    x_vals = list(range(0, 41))
    y_vals = []
    for s in x_vals:
        qs, tc, lossm, dec, scalem, pgc, ng, rg, nu, ru, re, gdis, ci = get_step_data(s)
        if show_resonant:
            val = ((rg - rod_g0)/rod_g0)*100.0 if opt_gwt else (((ru - rod_u0)/rod_u0)*100.0 if opt_ut else ((ci - c_idx0)/c_idx0)*100.0)
        else:
            val = (lossm / t_nom) * 100.0 if (opt_gwt or opt_ut) else ((D_in - dec) / D_in) * 100.0
        y_vals.append(round(val, 2))
    fig = go.Figure(go.Scatter(x=x_vals, y=y_vals, mode="lines+markers", name=ndt_choice))
    fig.add_vline(x=10, line_dash="dash", line_color="orange")
    fig.add_vline(x=25, line_dash="dash", line_color="red")
    fig.update_layout(xaxis_title="Defect (%)", yaxis_title="Value (%)", height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    eng_summary = (
        f"t_rem = {t_now*1000:.2f} mm (loss = {loss_now*1000:.2f} mm)"
        if (opt_gwt or opt_ut)
        else f"ID_eff = {d_eff_now*1000:.1f} mm (scale/side = {scale_side_now*1000:.1f} mm, Pg = {pg_now/1e5:.1f} bar)"
    )
    rep = (
        f"### DRVT Pipeline Integrity Report\n\n"
        f"* **Method:** {ndt_choice}\n"
        f"* **Dimensions:** OD={D_out_inch} in, t={t_nom_mm} mm, L={L_m} m\n"
        f"* **Defect Ratio:** {defect_pct}%\n"
        f"* **Status:** {st_txt}\n"
        f"* **Recommended Action:** {act_txt}\n"
        f"* **Engineering Reading:** `{eng_summary}`"
    )
    if show_resonant:
        res_str = (
            f"ROD_GWT = {rod_g_now:.4e} ({diff_g:+.2f}%)"
            if opt_gwt
            else (f"ROD_UT = {rod_u_now:.4e} ({diff_u:+.2f}%)" if opt_ut else f"C_index = {c_idx_now:.4e} ({diff_c:+.2f}%)")
        )
        rep += f"\n* **Resonant Reading (Research):** `{res_str}`"

    st.markdown(rep)

    if HAS_FPDF:
        try:
            pdf_data = build_pdf_bytes()
            st.download_button(
                "📥 تحميل التقرير الفني (PDF)" if is_ar else "📥 Download Technical Report (PDF)",
                data=pdf_data,
                file_name=f"DRVT_Technical_Report_{defect_pct}pct.pdf",
                mime="application/pdf",
            )
        except Exception:
            st.download_button(
                "📥 تحميل التقرير (.txt)" if is_ar else "📥 Download Report (.txt)",
                data=rep,
                file_name=f"DRVT_Report_{defect_pct}pct.txt",
                mime="text/plain",
            )
    else:
        st.download_button(
            "📥 تحميل التقرير (.txt)" if is_ar else "📥 Download Report (.txt)",
            data=rep,
            file_name=f"DRVT_Report_{defect_pct}pct.txt",
            mime="text/plain",
        )
