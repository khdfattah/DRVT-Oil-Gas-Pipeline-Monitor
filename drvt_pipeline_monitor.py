import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="DRVT Oil & Gas Pipeline Monitor", layout="wide")

lang = st.sidebar.radio("🌐 Language / اللغة", ("العربية", "English"), horizontal=True)
is_ar = (lang == "العربية")

if is_ar:
    st.markdown("<style>.main, .stSidebar { direction: rtl; text-align: right; } h1, h2, h3, p, div, label { text-align: right; }</style>", unsafe_allow_html=True)
else:
    st.markdown("<style>.main, .stSidebar { direction: ltr; text-align: left; } h1, h2, h3, p, div, label { text-align: left; }</style>", unsafe_allow_html=True)

st.title("🔬 DRVT Oil & Gas Pipeline Monitor")

if is_ar:
    st.info("**إعداد وتطوير:** د. خالد عبدالفتاح محمد عثمان | معهد مروي التكنولوجي، جامعة مروي التكنولوجية، السودان (`khdfattah@gmail.com`)")
    ndt_opts = ("الموجات الموجهة (GWT)", "الموجات فوق الصوتية (UT)", "الميكروويف الداخلي (EM)")
    ndt_choice = st.sidebar.selectbox("🔍 نوع الجهاز اللاتلافي (NDT):", ndt_opts)
    defect_pct = st.sidebar.slider("نسبة التآكل / الترسبات المستهدفة (%)", 0, 50, 15)
    exp_label = "⚙️ مدخلات الأنبوب والجهاز (للمطابقة مع الإكسيل)"
else:
    st.info("**Author:** Dr. Khalid Abdel Fattah Mohamed Osman | Merowe Institute of Technology, Merowe University of Technology, Sudan (`khdfattah@gmail.com`)")
    ndt_opts = ("Guided Wave Testing (GWT)", "Ultrasonic Thickness (UT)", "Internal Microwave (EM)")
    ndt_choice = st.sidebar.selectbox("🔍 NDT Device Type:", ndt_opts)
    defect_pct = st.sidebar.slider("Target Corrosion / Scaling (%)", 0, 50, 15)
    exp_label = "⚙️ Pipeline & Device Inputs (Excel Match)"

opt_gwt = (ndt_choice == ndt_opts[0])
opt_ut = (ndt_choice == ndt_opts[1])
opt_em = (ndt_choice == ndt_opts[2])

with st.sidebar.expander(exp_label, expanded=True):
    D_out_inch = st.number_input("D_out (in) / القطر الخارجي", value=12.75, step=0.25)
    t_nom_mm = st.number_input("t (mm) / السُمك الاسمي", value=9.53, step=0.01)
    L_m = st.number_input("L (m) / طول المقطع", value=10.0, step=1.0)
    P_watt = st.number_input("P (W) / قدرة الإرسال", value=50.0, step=5.0)
    Q_base = st.number_input("Q₀ / معامل الجودة", value=1000.0, step=100.0)
    f_gwt_khz = st.number_input("f_GWT (kHz)", value=32.0, step=1.0) if opt_gwt else 32.0
    f_ut_mhz = st.number_input("f_UT (MHz)", value=5.0, step=0.5) if opt_ut else 5.0
    f_em_ghz = st.number_input("f_EM (GHz)", value=2.4, step=0.1) if opt_em else 2.4
    Pg_bar = st.number_input("Pg (bar) / ضغط الغاز", value=50.0, step=5.0) if opt_em else 50.0
    eps_r = st.number_input("εr / ثابت العزل", value=1.05, step=0.01) if opt_em else 1.05

V_eq_m3 = 286.398e-27
denom_const = 2.0 * np.pi * 6.6261e-34 * (299792458.0 ** 2)
D_out = D_out_inch * 0.0254
t_nom = t_nom_mm / 1000.0
D_in = D_out - 2.0 * t_nom
Pg_pa = Pg_bar * 100000.0

lam_gwt = 5900.0 / (f_gwt_khz * 1000.0)
lam_ut = 5900.0 / (f_ut_mhz * 1e6)
lam_em = 299792458.0 / ((f_em_ghz * 1e9) * np.sqrt(eps_r))

def get_step_data(pct):
    r = pct / 100.0
    q = Q_base * (1.0 - 0.5 * r)
    t_c = t_nom * (1.0 - r)
    d_in_c = D_out - 2.0 * t_c
    d_eff_c = D_in * (1.0 - r)
    pg_c = Pg_pa * (1.0 + 0.4 * r)

    nres_g = ((np.pi / 4.0) * L_m * (D_out ** 2 - d_in_c ** 2)) / V_eq_m3
    rod_g = ((P_watt * q * (lam_gwt ** 2)) / denom_const) / nres_g

    nres_u = ((np.pi / 4.0) * (0.0127 ** 2) * t_c) / V_eq_m3
    rod_u = ((P_watt * q * (lam_ut ** 2)) / denom_const) / nres_u

    nres_e = ((np.pi / 4.0) * (d_eff_c ** 2) * L_m) / V_eq_m3
    rod_e = ((P_watt * q * (lam_em ** 2)) / denom_const) / nres_e
    gdi = 14369.0 / pg_c
    c_idx = rod_e / gdi

    return q, t_c, d_eff_c, nres_g, rod_g, nres_u, rod_u, rod_e, gdi, c_idx

_, _, _, _, rod_g0, _, rod_u0, _, _, c_idx0 = get_step_data(0)
q_now, t_now, d_now, _, rod_g_now, _, rod_u_now, rod_e_now, _, c_idx_now = get_step_data(defect_pct)

diff_g = ((rod_g_now - rod_g0) / rod_g0) * 100.0
diff_u = ((rod_u_now - rod_u0) / rod_u0) * 100.0
diff_c = ((c_idx_now - c_idx0) / c_idx0) * 100.0

tabs_titles = ("📊 النتائج والجداول", "📈 الرسم البياني", "📄 التقرير الفني") if is_ar else ("📊 Results & Tables", "📈 Chart", "📄 Technical Report")
tab1, tab2, tab3 = st.tabs(tabs_titles)

with tab1:
    st.subheader(f"نتيجة الفحص عند نسبة عيب: {defect_pct}%" if is_ar else f"Inspection Result at {defect_pct}% Defect")
    if opt_gwt:
        st.metric("ROD - GWT", f"{rod_g_now:.4e}", f"{diff_g:+.2f}%")
        st.caption(f"t = {t_now*1000:.2f} mm | Q = {q_now:.0f}")
    elif opt_ut:
        st.metric("ROD - UT", f"{rod_u_now:.4e}", f"{diff_u:+.2f}%")
        st.caption(f"t = {t_now*1000:.2f} mm | Q = {q_now:.0f}")
    else:
        st.metric("C_index - EM", f"{c_idx_now:.4e}", f"{diff_c:+.2f}%")
        st.caption(f"ID = {d_now*1000:.1f} mm | ROD_EM = {rod_e_now:.4e}")

    st.divider()
    rows = []
    for s in (0, 5, 10, 15, 20, 25, 30, 40):
        qs, tc, dc, ng, rg, nu, ru, re, gdis, ci = get_step_data(s)
        if opt_gwt:
            sh = ((rg - rod_g0) / rod_g0) * 100.0
            rows.append({"Defect (%)": f"{s}%", "Q": round(qs, 1), "t (mm)": round(tc*1000, 2), "N_res": f"{ng:.3e}", "ROD (GWT)": f"{rg:.4e}", "Shift (%)": f"{sh:+.2f}%"})
        elif opt_ut:
            sh = ((ru - rod_u0) / rod_u0) * 100.0
            rows.append({"Defect (%)": f"{s}%", "Q": round(qs, 1), "t (mm)": round(tc*1000, 2), "N_res": f"{nu:.3e}", "ROD (UT)": f"{ru:.4e}", "Shift (%)": f"{sh:+.2f}%"})
        else:
            sh = ((ci - c_idx0) / c_idx0) * 100.0
            rows.append({"Defect (%)": f"{s}%", "Q": round(qs, 1), "ID (mm)": round(dc*1000, 1), "ROD (EM)": f"{re:.4e}", "GDI": f"{gdis:.3e}", "C_index": f"{ci:.4e}", "Shift (%)": f"{sh:+.2f}%"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

with tab2:
    x_vals = list(range(0, 41))
    y_vals = []
    for s in x_vals:
        _, _, _, _, rg, _, ru, _, _, ci = get_step_data(s)
        val = ((rg - rod_g0)/rod_g0)*100.0 if opt_gwt else (((ru - rod_u0)/rod_u0)*100.0 if opt_ut else ((ci - c_idx0)/c_idx0)*100.0)
        y_vals.append(round(val, 2))
    fig = go.Figure(go.Scatter(x=x_vals, y=y_vals, mode="lines+markers", name=ndt_choice))
    fig.update_layout(xaxis_title="Defect (%)", yaxis_title="Deviation (%)", height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    if defect_pct < 10:
        st_txt = "حالة سليمة / مستقرة" if is_ar else "Healthy / Stable Condition"
    elif defect_pct < 25:
        st_txt = "تنبيه مبكر (ترقق / ترسبات)" if is_ar else "Early Warning (Thinning / Scaling)"
    else:
        st_txt = "حالة حرجة (تدخل عاجل)" if is_ar else "Critical Condition (Immediate Action)"

    val_str = f"ROD_GWT = {rod_g_now:.4e} ({diff_g:+.2f}%)" if opt_gwt else (f"ROD_UT = {rod_u_now:.4e} ({diff_u:+.2f}%)" if opt_ut else f"C_index = {c_idx_now:.4e} ({diff_c:+.2f}%)")
    rep = f"### DRVT Pipeline Integrity Report\n**Author:** Dr. Khalid Abdel Fattah Mohamed Osman — Merowe Institute of Technology, Merowe University of Technology, Sudan\n\n* **Method:** {ndt_choice}\n* **Dimensions:** OD={D_out_inch} in, t={t_nom_mm} mm, L={L_m} m\n* **Defect Ratio:** {defect_pct}%\n* **Status:** {st_txt}\n* **Result:** `{val_str}`"
    st.markdown(rep)
    st.download_button("📥 Download Report (.txt)", data=rep, file_name=f"DRVT_Report_{defect_pct}pct.txt")

st.divider()
st.caption("© DRVT Oil & Gas Pipeline Monitor | Dr. Khalid Abdel Fattah Mohamed Osman — Merowe Institute of Technology, Merowe University of Technology, Sudan")
