import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from fpdf import FPDF

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
    D_out_inch = st.number_input(
        "D_out (in) / القطر الخارجي [2–48 in]",
        min_value=2.0,
        max_value=48.0,
        value=12.75,
        step=0.25,
    )
    t_nom_mm = st.number_input(
        "t_nom (mm) / السُمك الاسمي [3–40 mm]",
        min_value=3.0,
        max_value=40.0,
        value=12.70,
        step=0.10,
    )
    L_m = st.number_input(
        "L (m) / طول المقطع [1–100 m]",
        min_value=1.0,
        max_value=100.0,
        value=10.0,
        step=1.0,
    )
    dp_mm = st.number_input(
        "d_p (mm) / قطر مجس UT [5–50 mm]",
        min_value=5.0,
        max_value=50.0,
        value=15.0,
        step=1.0,
    ) if opt_ut else 15.0

    P_watt = st.number_input(
        "P (W) / قدرة الإرسال [0.005–10 W]",
        min_value=0.005,
        max_value=10.0,
        value=0.05,
        step=0.01,
        format="%.3f",
    )
    Q_base = st.number_input(
        "Q₀ / معامل الجودة الأساسي [100–5000]",
        min_value=100.0,
        max_value=5000.0,
        value=1000.0,
        step=50.0,
    )
    f_gwt_khz = st.number_input(
        "f_GWT (kHz) [20–100 kHz]",
        min_value=20.0,
        max_value=100.0,
        value=50.0,
        step=1.0,
    ) if opt_gwt else 50.0

    f_ut_mhz = st.number_input(
        "f_UT (MHz) [1–15 MHz]",
        min_value=1.0,
        max_value=15.0,
        value=5.0,
        step=0.5,
    ) if opt_ut else 5.0

    f_em_ghz = st.number_input(
        "f_EM (GHz) [0.9–10 GHz]",
        min_value=0.9,
        max_value=10.0,
        value=2.4,
        step=0.1,
    ) if opt_em else 2.4

    Pg_bar = st.number_input(
        "Pg (bar) / ضغط الغاز [5–150 bar]",
        min_value=5.0,
        max_value=150.0,
        value=50.0,
        step=5.0,
    ) if opt_em else 50.0

    eps_r = st.number_input(
        "εr / ثابت العزل [1.0001–2.50]",
        min_value=1.0001,
        max_value=2.50,
        value=1.0006,
        step=0.001,
        format="%.4f",
    ) if opt_em else 1.0006

# الثوابت الفيزيائية لنظرية DRVT والوسط الفولاذي
V_eq_m3 = 286.398e-27
h_const = 6.6261e-34
c_const = 299792458.0
vs_steel = 5900.0
denom_const = 2.0 * np.pi * h_const * (c_const ** 2)

# التحويل إلى وحدات SI
D_out = D_out_inch * 0.0254
t_nom = t_nom_mm / 1000.0
D_in = max(D_out - 2.0 * t_nom, 1e-4)
dp_m = dp_mm / 1000.0
Pg_pa = Pg_bar * 100000.0

# الأطوال الموجية
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
            "استمرار المراقبة الدورية المجدولة دون تدخل طارئ، مع توثيق القراءات ضمن سجل السلامة."
            if is_ar
            else "Continue scheduled routine monitoring with no urgent intervention; log baseline readings."
        )
        action_en = "Continue scheduled routine monitoring with no urgent intervention; log baseline readings."
        level = "ok"
    elif pct < 25:
        status = "تنبيه مبكر (ترقق أو ترسبات)" if is_ar else "Early Warning (Thinning / Scaling)"
        status_en = "Early Warning (Thinning / Scaling)"
        action = (
            "إجراء فحص موضعي تأكيدي (UT/Visual/Pigging) ومراجعة معدل التآكل أو الترسبات وضغط التشغيل لتحديد الجدولة الوقائية."
            if is_ar
            else "Perform confirmatory localized inspection (UT/pigging) and review corrosion/scaling rate and operating pressure."
        )
        action_en = "Perform confirmatory localized inspection (UT/pigging) and review corrosion/scaling rate and operating pressure."
        level = "warn"
    else:
        status = "حالة حرجة (تدخل هندسي عاجل)" if is_ar else "Critical Condition (Urgent Action)"
        status_en = "Critical Condition (Urgent Action)"
        action = (
            "رفع تنبيه تشغيلي عاجل، وتقييم السلامة الإنشائية وفق معايير التصميم، والنظر في خفض الضغط أو عزل المقطع وإصلاحه/تنظيفه."
            if is_ar
            else "Raise urgent integrity alert, run fitness-for-service/code assessment, and evaluate derating, isolation, or repair/cleaning."
        )
        action_en = "Raise urgent integrity alert, run fitness-for-service/code assessment, and evaluate derating, isolation, or repair/cleaning."
        level = "crit"
    return status, status_en, action, action_en, level


_, _, _, _, _, _, _, rod_g0, _, rod_u0, _, _, c_idx0 = get_step_data(0)
q_now, t_now, loss_now, d_eff_now, scale_side_now, pg_now, nres_g_now, rod_g_now, nres_u_now, rod_u_now, rod_e_now, gdi_now, c_idx_now = get_step_data(defect_pct)

diff_g = ((rod_g_now - rod_g0) / rod_g0) * 100.0
diff_u = ((rod_u_now - rod_u0) / rod_u0) * 100.0
diff_c = ((c_idx_now - c_idx0) / c_idx0) * 100.0

st_txt, st_en, act_txt, act_en, lvl_txt = get_decision_info(defect_pct)


def build_pdf_report():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # فحص وجود خط يدعم العربية؛ وإلا استخدام خط لاتيني قياسي آمن
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    unicode_font = next((p for p in font_candidates if os.path.exists(p)), None)

    if unicode_font:
        pdf.add_font("CustomFont", "", unicode_font)
        pdf.set_font("CustomFont", size=14)
        pdf.cell(0, 10, "DRVT Pipeline Integrity Technical Report", ln=True)
        pdf.set_font("CustomFont", size=10)
        lines = [
            "Author: Dr. Khalid Abdel Fattah Mohamed Osman | Merowe University of Technology, Sudan",
            f"NDT Method: {ndt_choice}",
            f"Pipeline Dimensions: OD = {D_out_inch:.2f} in, t_nom = {t_nom_mm:.2f} mm, L = {L_m:.1f} m",
            f"Defect Ratio: {defect_pct}%",
            f"Engineering Status: {st_en}",
            f"Remaining Wall Thickness (t_rem): {t_now * 1000:.2f} mm (Loss: {loss_now * 1000:.2f} mm)",
            f"Effective Inner Diameter (ID_eff): {d_eff_now * 1000:.1f} mm (Scale/side: {scale_side_now * 1000:.1f} mm)",
            f"Operating Gas Pressure (Pg): {pg_now / 1e5:.1f} bar",
            f"Recommended Action: {act_en}",
        ]
        if show_resonant:
            lines.extend([
                f"DRVT Resonant Metrics (Research): ROD_GWT={rod_g_now:.4e} ({diff_g:+.2f}%), "
                f"ROD_UT={rod_u_now:.4e} ({diff_u:+.2f}%), C_index={c_idx_now:.4e} ({diff_c:+.2f}%)",
            ])
        lines.append(
            "Note: DRVT in NDT is a theoretical/extrapolative model requiring experimental calibration "
            "and does not replace engineering codes or minimum wall calculations."
        )
        for line in lines:
            pdf.multi_cell(0, 7, line)
    else:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "DRVT Pipeline Integrity Technical Report", ln=True)
        pdf.set_font("Helvetica", size=10)
        method_ascii = (
            "Guided Wave Testing (GWT)" if opt_gwt
            else ("Ultrasonic Thickness (UT)" if opt_ut else "Internal Microwave (EM)")
        )
        safe_lines = [
            "Author: Dr. Khalid Abdel Fattah Mohamed Osman | Merowe University of Technology, Sudan",
            f"NDT Method: {method_ascii}",
            f"Dimensions: OD = {D_out_inch:.2f} in, t_nom = {t_nom_mm:.2f} mm, L = {L_m:.1f} m",
            f"Defect Ratio: {defect_pct}%",
            f"Engineering Status: {st_en}",
            f"Remaining Wall Thickness: {t_now * 1000:.2f} mm (Wall Loss: {loss_now * 1000:.2f} mm)",
            f"Effective Inner Diameter: {d_eff_now * 1000:.1f} mm (Scale/side: {scale_side_now * 1000:.1f} mm)",
            f"Gas Pressure: {pg_now / 1e5:.1f} bar",
            f"Recommended Action: {act_en}",
        ]
        if show_resonant:
            safe_lines.append(
                f"Resonant Metrics: ROD_GWT={rod_g_now:.4e} ({diff_g:+.2f}%), "
                f"ROD_UT={rod_u_now:.4e} ({diff_u:+.2f}%), C_index={c_idx_now:.4e} ({diff_c:+.2f}%)"
            )
        safe_lines.append(
            "Note: DRVT in NDT is a theoretical/extrapolative model requiring experimental calibration "
            "and does not replace engineering codes."
        )
        for line in safe_lines:
            clean_line = line.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 7, clean_line)

    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")


tabs_titles = (
    ("📊 النتائج والقرارات", "📈 الرسم البياني", "📄 التقرير الفني (PDF)")
    if is_ar
    else ("📊 Results & Decisions", "📈 Chart", "📄 Technical Report (PDF)")
)
tab1, tab2, tab3 = st.tabs(tabs_titles)

with tab1:
    st.subheader(
        f"لوحة قراءة المهندس عند نسبة عيب: {defect_pct}%"
        if is_ar
        else f"Pipeline Engineer Decision View at {defect_pct}% Defect"
    )

    if lvl_txt == "ok":
        st.success(f"**{st_txt}** — {act_txt}")
    elif lvl_txt == "warn":
        st.warning(f"**{st_txt}** — {act_txt}")
    else:
        st.error(f"**{st_txt}** — {act_txt}")

    c1, c2, c3 = st.columns(3)
    if opt_gwt or opt_ut:
        c1.metric(
            "السُمك المتبقي / Remaining t" if is_ar else "Remaining Thickness (t)",
            f"{t_now * 1000:.2f} mm",
            f"-{loss_now * 1000:.2f} mm loss",
        )
        c2.metric(
            "الفقد في الجدار / Wall Loss" if is_ar else "Wall Loss",
            f"{loss_now * 1000:.2f} mm",
            f"{defect_pct}% of nominal",
        )
        c3.metric(
            "معامل الجودة / Q Factor" if is_ar else "Quality Factor (Q)",
            f"{q_now:.0f}",
        )
    else:
        c1.metric(
            "القطر الداخلي الفعلي / Effective ID" if is_ar else "Effective ID (Deff)",
            f"{d_eff_now * 1000:.1f} mm",
            f"{scale_side_now * 1000:.1f} mm scale/side",
        )
        c2.metric(
            "سُمك الترسبات المكافئ / Scale/Side" if is_ar else "Equivalent Scale / Side",
            f"{scale_side_now * 1000:.1f} mm",
            f"{defect_pct}% ID reduction",
        )
        c3.metric(
            "ضغط الغاز / Gas Pressure" if is_ar else "Gas Pressure (Pg)",
            f"{pg_now / 1e5:.1f} bar",
        )

    if show_resonant:
        st.markdown("#### 🔬 القراءات الرنينية (DRVT Resonant Metrics — للبحث)")
        r1, r2, r3 = st.columns(3)
        if opt_gwt:
            r1.metric("ROD - GWT", f"{rod_g_now:.4e}", f"{diff_g:+.2f}%")
            r2.metric("N_res (GWT)", f"{nres_g_now:.3e}")
            r3.metric("λ_GWT", f"{lam_gwt:.3f} m")
        elif opt_ut:
            r1.metric("ROD - UT", f"{rod_u_now:.4e}", f"{diff_u:+.2f}%")
            r2.metric("N_res (UT)", f"{nres_u_now:.3e}")
            r3.metric("λ_UT", f"{lam_ut * 1000:.2f} mm")
        else:
            r1.metric("C_index - EM", f"{c_idx_now:.4e}", f"{diff_c:+.2f}%")
            r2.metric("ROD_EM", f"{rod_e_now:.4e}")
            r3.metric("GDI", f"{gdi_now:.3e}")

    st.caption(
        "ملاحظة منهجية: تطبيق DRVT في اختبارات NDT إطار نظري استقرائي يتطلب معايرة وتحققاً تجريبياً، ولا يغني عن الأكواد الهندسية وحسابات حد السُمك المسموح."
        if is_ar
        else "Methodological note: DRVT in NDT is a theoretical/extrapolative model requiring experimental calibration and does not replace engineering codes or minimum wall calculations."
    )

    st.divider()
    rows = []
    for s in (0, 5, 10, 15, 20, 25, 30, 40):
        qs, tc, lossm, dec, scalem, pgc, ng, rg, nu, ru, re, gdis, ci = get_step_data(s)
        sts, _, _, _, _ = get_decision_info(s)
        if opt_gwt:
            row = {
                "Defect (%)": f"{s}%",
                "t_rem (mm)": round(tc * 1000, 2),
                "Loss (mm)": round(lossm * 1000, 2),
                "Q": round(qs, 0),
                "Decision": sts,
            }
            if show_resonant:
                row["ROD (GWT)"] = f"{rg:.4e}"
                row["Shift (%)"] = f"{((rg - rod_g0) / rod_g0) * 100.0:+.2f}%"
            rows.append(row)
        elif opt_ut:
            row = {
                "Defect (%)": f"{s}%",
                "t_rem (mm)": round(tc * 1000, 2),
                "Loss (mm)": round(lossm * 1000, 2),
                "Q": round(qs, 0),
                "Decision": sts,
            }
            if show_resonant:
                row["ROD (UT)"] = f"{ru:.4e}"
                row["Shift (%)"] = f"{((ru - rod_u0) / rod_u0) * 100.0:+.2f}%"
            rows.append(row)
        else:
            row = {
                "Defect (%)": f"{s}%",
                "ID_eff (mm)": round(dec * 1000, 1),
                "Scale/side (mm)": round(scalem * 1000, 1),
                "Pg (bar)": round(pgc / 1e5, 1),
                "Decision": sts,
            }
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
            val = (
                ((rg - rod_g0) / rod_g0) * 100.0
                if opt_gwt
                else (((ru - rod_u0) / rod_u0) * 100.0 if opt_ut else ((ci - c_idx0) / c_idx0) * 100.0)
            )
        else:
            val = (lossm / t_nom) * 100.0 if (opt_gwt or opt_ut) else ((D_in - dec) / D_in) * 100.0
        y_vals.append(round(val, 2))

    y_label = (
        "Resonant Deviation (%)"
        if show_resonant
        else ("Wall Loss (%)" if (opt_gwt or opt_ut) else "ID Reduction (%)")
    )
    fig = go.Figure(go.Scatter(x=x_vals, y=y_vals, mode="lines+markers", name=ndt_choice))
    fig.add_vline(x=10, line_dash="dash", line_color="orange", annotation_text="10%")
    fig.add_vline(x=25, line_dash="dash", line_color="red", annotation_text="25%")
    fig.update_layout(xaxis_title="Defect (%)", yaxis_title=y_label, height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    eng_summary = (
        f"t_rem = {t_now*1000:.2f} mm (loss = {loss_now*1000:.2f} mm)"
        if (opt_gwt or opt_ut)
        else f"ID_eff = {d_eff_now*1000:.1f} mm (scale/side = {scale_side_now*1000:.1f} mm, Pg = {pg_now/1e5:.1f} bar)"
    )
    rep = (
        f"### DRVT Pipeline Integrity Report\n**Technical Report**\n\n"
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
    pdf_bytes = build_pdf_report()
    st.download_button(
        "📥 Download Technical Report (PDF)" if not is_ar else "📥 تحميل التقرير الفني (PDF)",
        data=pdf_bytes,
        file_name=f"DRVT_Technical_Report_{defect_pct}pct.pdf",
        mime="application/pdf",
    )

st.divider()
st.caption(
    "© DRVT Oil & Gas Pipeline Monitor | Dr. Khalid Abdel Fattah Mohamed Osman — Merowe Institute of Technology, Merowe University of Technology, Sudan"
)
