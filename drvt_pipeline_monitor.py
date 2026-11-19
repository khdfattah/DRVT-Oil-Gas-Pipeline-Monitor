import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="DRVT Oil & Gas Pipeline Monitor", layout="wide")

lang = st.sidebar.radio("🌐 Language / اللغة", ("العربية", "English"), horizontal=True)
is_ar = lang == "العربية"

if is_ar:
    st.markdown("<style>.main, .stSidebar { direction: rtl; text-align: right; } h1, h2, h3, p, div, label { text-align: right; }</style>", unsafe_allow_html=True)
else:
    st.markdown("<style>.main, .stSidebar { direction: ltr; text-align: left; } h1, h2, h3, p, div, label { text-align: left; }</style>", unsafe_allow_html=True)

T = {
    "title": "🔬 DRVT Oil & Gas Pipeline Monitor",
    "author_box": "**إعداد وتطوير:** د. خالد عبدالفتاح محمد عثمان | معهد مروي التكنولوجي، جامعة مروي التكنولوجية، السودان (`khdfattah@gmail.com`)" if is_ar else "**Author:** Dr. Khalid Abdel Fattah Mohamed Osman | Merowe Institute of Technology, Merowe University of Technology, Sudan (`khdfattah@gmail.com`)",
    "ndt_select_label": "🔍 نوع الجهاز اللاتلافي (NDT):" if is_ar else "🔍 NDT Device Type:",
    "ndt_options": ("الموجات الموجهة (GWT)", "الموجات فوق الصوتية (UT)", "الميكروويف الداخلي (EM)") if is_ar else ("Guided Wave Testing (GWT)", "Ultrasonic Thickness (UT)", "Internal Microwave (EM)"),
    "defect": "نسبة التآكل / الترسبات المستهدفة (%)" if is_ar else "Target Corrosion / Scaling (%)",
    "exp_inputs": "⚙️ مدخلات الأنبوب والجهاز (للمطابقة مع الإكسيل)" if is_ar else "⚙️ Pipeline & Device Inputs (Excel Match)",
    "d_out": "القطر الخارجي (بوصة)" if is_ar else "Outer Diameter D_out (in)",
    "t_nom": "سُمك الجدار الاسمي (مم)" if is_ar else "Nominal Wall Thickness t (mm)",
    "l_m": "طول المقطع المفحوص (متر)" if is_ar else "Inspected Length L (m)",
    "p_watt": "قدرة الإرسال P (واط)" if is_ar else "Transmitted Power P (W)",
    "q_base": "معامل الجودة المرجعي Q₀" if is_ar else "Baseline Quality Factor Q₀",
    "f_gwt": "تردد GWT (كيلوهرتز)" if is_ar else "GWT Frequency (kHz)",
    "f_ut": "تردد UT (ميجاهرتز)" if is_ar else "UT Frequency (MHz)",
    "f_em": "تردد EM (جيجاهرتز)" if is_ar else "EM Frequency (GHz)",
    "pg_bar": "ضغط الغاز الطبيعي (بار)" if is_ar else "Gas Pressure Pg (bar)",
    "eps_r": "ثابت العزل εr" if is_ar else "Permittivity εr",
    "tabs": ("📊 النتائج والجداول", "📈 الرسم البياني", "📄 التقرير الفني") if is_ar else ("📊 Results & Tables", "📈 Chart", "📄 Technical Report"),
    "res_header": "نتيجة الفحص عند نسبة عيب:" if is_ar else "Inspection Result at Defect Ratio:",
    "m_gwt": "ROD - الموجات الموجهة (GWT)" if is_ar else "ROD - Guided Wave (GWT)",
    "c_gwt": "سُمك الجدار المتبقي:" if is_ar else "Remaining Wall Thickness:",
    "m_ut": "ROD - الموجات فوق الصوتية (UT)" if is_ar else "ROD - Ultrasonic (UT)",
    "c_ut": "معامل الجودة الفعلي Q:" if is_ar else "Effective Quality Factor Q:",
    "m_em": "مؤشر الانسداد (C_index - EM)" if is_ar else "Clogging Index (C_index - EM)",
    "c_em": "القطر الداخلي الفعلي:" if is_ar else "Effective Inner Diameter:",
    "unit_mm": "مم" if is_ar else "mm",
    "tbl_header": "جدول المحاكاة المتدرج (مطابق لملف الإكسيل)" if is_ar else "Progressive Simulation Table (Matches Excel)",
    "chart_header": "منحنى استجابة الجهاز لتفاقم الصدأ والترسبات" if is_ar else "Device Response vs. Corrosion & Scaling Progression",
    "rep_header": "التقرير الفني لحالة الأنبوب" if is_ar else "Technical Pipeline Integrity Report",
    "dl_btn": "📥 تحميل التقرير (.txt)" if is_ar else "📥 Download Report (.txt)",
}

st.title(T["title"])
st.info(T["author_box"])

# الشريط الجانبي
ndt_choice = st.sidebar.selectbox(T["ndt_select_label"], T["ndt_options"])
defect_pct = st.sidebar.slider(T["defect"], 0, 50, 15)

opt_gwt = ndt_choice == T["ndt_options"][0]
opt_ut = ndt_choice == T["ndt_options"][1]
opt_em = ndt_choice == T["ndt_options"][2]

# قسم المدخلات الكاملة للمطابقة مع ملف الإكسيل
with st.sidebar.expander(T["exp_inputs"], expanded=True):
    D_out_inch = st.number_input(T["d_out"], value=12.75, step=0.25)
    t_nom_mm = st.number_input(T["t_nom"], value=9.53, step=0.01)
    L_m = st.number_input(T["l_m"], value=10.0, step=1.0)
    P_watt = st.number_input(T["p_watt"], value=50.0, step=5.0)
    Q_base = st.number_input(T["q_base"], value=1000.0, step=100.0)
    
    f_gwt_khz = 32.0
    f_ut_mhz = 5.0
    f_em_ghz = 2.4
    Pg_bar = 50.0
    eps_r = 1.05
    
    if opt_gwt:
        f_gwt_khz = st.number_input(T["f_gwt"], value=32.0, step=1.0)
    elif opt_ut:
        f_ut_mhz = st.number_input(T["f_ut"], value=5.0, step=0.5)
    elif opt_em:
        f_em_ghz = st.number_input(T["f_em"], value=2.4, step=0.1)
        Pg_bar = st.number_input(T["pg_bar"], value=50.0, step=5.0)
        eps_r = st.number_input(T["eps_r"], value=1.05, step=0.01)

# الثوابت الفيزيائية المطابقة للإكسيل
V_eq_m3 = 286.398 * 1e-27
h = 6.6261e-34
c = 299792458.0
v_s = 5900.0
d_p = 0.0127
denom_const = 2.0 * np.pi * h * (c ** 2)

D_out = D_out_inch * 0.0254
t_nom = t_nom_mm / 1000.0
D_in = D_out - 2.0 * t_nom
Pg_pa = Pg_bar * 100000.0

lam_gwt = v_s / (f_gwt_khz * 1000.0)
lam_ut = v_s / (f_ut_mhz * 1e6)
lam_em = c / ((f_em_ghz * 1e9) * np.sqrt(eps_r))

def calc_metrics(pct):
    r = pct / 100.0
    q = Q_base * (1.0 - 0.5 * r)
    t_c = t_nom * (1.0 - r)
    d_in_c = D_out - 2.0 * t_c
    d_eff_c = D_in * (1.0 - r)
    pg_c = Pg_pa * (1.0 + 0.4 * r)

    # 1. GWT
    vcav_g = (np.pi / 4.0) * L_m * (D_out ** 2 - d_in_c ** 2)
    nres_g = vcav_g / V_eq_m3
    nwav_g = (P_watt * q * (lam_gwt ** 2)) / denom_const
    rod_g = nwav_g / nres_g

    # 2. UT
    vcav_u = (np.pi / 4.0) * (d_p ** 2) * t_c
    nres_u = vcav_u / V_eq_m3
    nwav_u = (P_watt * q * (lam_ut ** 2)) / denom_const
    rod_u = nwav_u / nres_u

    # 3. EM
    vcav_e = (np.pi / 4.0) * (d_eff_c ** 2) * L_m
    nres_e = vcav_e / V_eq_m3
    nph_e = (P_watt * q * (lam_em ** 2)) / denom_const
    rod_e = nph_e / nres_e
    gdi = 14369.0 / pg_c
    c_idx = rod_e / gdi

    return q, t_c, d_eff_c, pg_c, nres_g, rod_g, nres_u, rod_u, nres_e, rod_e, gdi, c_idx

_, _, _, _, _, ROD_gwt_0, _, ROD_ut_0, _, ROD_em_0, _, C_index_0 = calc_metrics(0)
Q_curr, t_curr_gwt, D_eff_em, Pg_curr, Nres_g, ROD_gwt, Nres_u, ROD_ut, Nres_e, ROD_em, GDI_curr, C_index = calc_metrics(defect_pct)

diff_gwt = ((ROD_gwt - ROD_gwt_0) / ROD_gwt_0) * 100.0
diff_ut = ((ROD_ut - ROD_ut_0) / ROD_ut_0) * 100.0
diff_c = ((C_index - C_index_0) / C_index_0) * 100.0

tab1, tab2, tab3 = st.tabs(T["tabs"])

with tab1:
    st.subheader(f"{T['res_header']} {defect_pct}%")

    if opt_gwt:
        st.metric(T["m_gwt"], f"{ROD_gwt:.4e}", f"{diff_gwt:+.2f}%")
        st.caption(f"{T['c_gwt']} {t_curr_gwt*1000:.2f} {T['unit_mm']} | Q = {Q_curr:.0f}")
    elif opt_ut:
        st.metric(T["m_ut"], f"{ROD_ut:.4e}", f"{diff_ut:+.2f}%")
        st.caption(f"{T['c_gwt']} {t_curr_gwt*1000:.2f} {T['unit_mm']} | Q = {Q_curr:.0f}")
    elif opt_em:
        st.metric(T["m_em"], f"{C_index:.4e}", f"{diff_c:+.2f}%")
        st.caption(f"{T['c_em']} {D_eff_em*1000:.1f} {T['unit_mm']} | ROD_EM = {ROD_em:.4e}")

    st.divider()
    st.subheader(T["tbl_header"])
    rows = []
    # نفس نسب الإكسيل (0% إلى 30% بخطوة 5% ثم 40%)
    for s in (0, 5, 10, 15, 20, 25, 30, 40):
        q_s, t_c, d_eff_c, pg_c, nres_g, rod_g, nres_u, rod_u, nres_e, rod_e, gdi_s, c_idx = calc_metrics(s)
        
        row_dict = {}
        if is_ar:
            row_dict["نسبة العيب (%)"] = f"{s}%"
            row_dict["معامل الجودة Q"] = round(q_s, 1)
            if opt_gwt:
                shift_g = ((rod_g - ROD_gwt_0) / ROD_gwt_0) * 100.0
                row_dict["السُمك المتبقي (مم)"] = round(t_c * 1000, 2)
                row_dict["سعة التخزين N_res"] = f"{nres_g:.3e}"
                row_dict["ROD (GWT)"] = f"{rod_g:.4e}"
                row_dict["الانحراف (%)"] = f"{shift_g:+.2f}%"
            elif opt_ut:
                shift_u = ((rod_u - ROD_ut_0) / ROD_ut_0) * 100.0
                row_dict["السُمك المتبقي (مم)"] = round(t_c * 1000, 2)
                row_dict["سعة التخزين N_res"] = f"{nres_u:.3e}"
                row_dict["ROD (UT)"] = f"{rod_u:.4e}"
                row_dict["الانحراف (%)"] = f"{shift_u:+.2f}%"
            elif opt_em:
                shift_c = ((c_idx - C_index_0) / C_index_0) * 100.0
                row_dict["القطر الفعلي (مم)"] = round(d_eff_c * 1000, 1)
                row_dict["ROD (EM)"] = f"{rod_e:.4e}"
                row_dict["مؤشر الغاز GDI"] = f"{gdi_s:.3e}"
                row_dict["مؤشر الانسداد C_index"] = f"{c_idx:.4e}"
                row_dict["الانحراف (%)"] = f"{shift_c:+.2f}%"
        else:
            row_dict["Defect (%)"] = f"{s}%"
            row_dict["Quality Factor Q"] = round(q_s, 1)
            if opt_gwt:
                shift_g = ((rod_g - ROD_gwt_0) / ROD_gwt_0) * 100.0
                row_dict["Remaining Wall (mm)"] = round(t_c * 1000, 2)
                row_dict["N_res"] = f"{nres_g:.3e}"
                row_dict["ROD (GWT)"] = f"{rod_g:.4e}"
                row_dict["Deviation (%)"] = f"{shift_g:+.2f}%"
            elif opt_ut:
                shift_u = ((rod_u - ROD_ut_0) / ROD_ut_0) * 100.0
                row_dict["Remaining Wall (mm)"] = round(t_c * 1000, 2)
                row_dict["N_res"] = f"{nres_u:.3e}"
                row_dict["ROD (UT)"] = f"{rod_u:.4e}"
                row_dict["Deviation (%)"] = f"{shift_u:+.2f}%"
            elif opt_em:
                shift_c = ((c_idx - C_index_0) / C_index_0) * 100.0
                row_dict["Effective ID (mm)"] = round(d_eff_c * 1000, 1)
                row_dict["ROD (EM)"] = f"{rod_e:.4e}"
                row_dict["GDI"] = f"{gdi_s:.3e}"
                row_dict["C_index"] = f"{c_idx:.4e}"
                row_dict["Deviation (%)"] = f"{shift_c:+.2f}%"
        rows.append(row_dict)

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

with tab2:
    st.subheader(T["chart_header"])
    x_vals = list(range(0, 41, 1))
    y_vals = []
    for s in x_vals:
