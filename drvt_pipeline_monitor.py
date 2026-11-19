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
    "sb_header": "⚙️ إعدادات الفحص والأنبوب" if is_ar else "⚙️ Inspection & Pipeline Settings",
    "ndt_select_label": "🔍 اختر تقنية الفحص (NDT):" if is_ar else "🔍 Select NDT Inspection Method:",
    "ndt_options": ("الكل (مقارنة شاملة)", "الموجات الموجهة (GWT)", "الموجات فوق الصوتية (UT)", "الميكروويف الداخلي (EM)") if is_ar else ("All Methods (Comparison)", "Guided Wave Testing (GWT)", "Ultrasonic Thickness (UT)", "Internal Microwave (EM)"),
    "sb_pipe": "1. أبعاد الأنبوب القياسي" if is_ar else "1. Standard Pipeline Dimensions",
    "d_out": "القطر الخارجي (بوصة)" if is_ar else "Outer Diameter D_out (inches)",
    "t_nom": "سُمك الجدار الاسمي (مم)" if is_ar else "Nominal Wall Thickness t (mm)",
    "l_m": "طول المقطع المفحوص (متر)" if is_ar else "Inspected Section Length L (m)",
    "sb_ndt": "2. معاملات جهاز الفحص" if is_ar else "2. NDT Device Parameters",
    "p_watt": "قدرة الإرسال P (واط)" if is_ar else "Transmitted Power P (W)",
    "q_base": "معامل الجودة المرجعي Q₀" if is_ar else "Baseline Quality Factor Q₀",
    "f_gwt": "تردد الموجات الموجهة GWT (كيلوهرتز)" if is_ar else "Guided Wave Frequency GWT (kHz)",
    "f_ut": "تردد الموجات فوق الصوتية UT (ميجاهرتز)" if is_ar else "Ultrasonic Frequency UT (MHz)",
    "f_em": "تردد الميكروويف EM (جيجاهرتز)" if is_ar else "Microwave Frequency EM (GHz)",
    "sb_op": "3. ظروف التشغيل والعيوب" if is_ar else "3. Operating Conditions & Defects",
    "pg_bar": "ضغط الغاز الطبيعي (بار)" if is_ar else "Gas Pressure Pg (bar)",
    "eps_r": "ثابت العزل للغاز εr" if is_ar else "Relative Permittivity εr",
    "defect": "نسبة التآكل / الترسبات المستهدفة (%)" if is_ar else "Target Corrosion / Scaling Ratio (%)",
    "tabs": ("📊 لوحة المحاكاة والنتائج", "📈 الرسوم البيانية", "📄 التقرير الفني") if is_ar else ("📊 Simulation Dashboard", "📈 Response Charts", "📄 Technical Report"),
    "res_header": "نتائج الفحص عند نسبة تآكل / ترسبات:" if is_ar else "Inspection Results at Defect Ratio:",
    "m_gwt": "ROD - الموجات الموجهة (GWT)" if is_ar else "ROD - Guided Wave (GWT)",
    "c_gwt": "سُمك الجدار المتبقي:" if is_ar else "Remaining Wall Thickness:",
    "m_ut": "ROD - الموجات فوق الصوتية (UT)" if is_ar else "ROD - Ultrasonic (UT)",
    "c_ut": "معامل الجودة الفعلي Q:" if is_ar else "Effective Quality Factor Q:",
    "m_em": "مؤشر الانسداد (C_index - EM)" if is_ar else "Clogging Index (C_index - EM)",
    "c_em": "القطر الداخلي الفعلي:" if is_ar else "Effective Inner Diameter:",
    "unit_mm": "مم" if is_ar else "mm",
    "tbl_header": "جدول مقارنة السيناريوهات المتدرجة (0% إلى 40%)" if is_ar else "Progressive Defect Scenarios Table (0% to 40%)",
    "chart_header": "منحنى استجابة مؤشرات DRVT لتفاقم الصدأ والترسبات" if is_ar else "DRVT Indicators Response vs. Corrosion & Scaling Progression",
    "rep_header": "التقرير الفني لحالة مراقبة الأنابيب" if is_ar else "Technical Pipeline Integrity Report",
    "dl_btn": "📥 تحميل التقرير الفني (ملف نصي)" if is_ar else "📥 Download Technical Report (.txt)",
}

st.title(T["title"])
st.info(T["author_box"])

st.sidebar.header(T["sb_header"])
ndt_choice = st.sidebar.selectbox(T["ndt_select_label"], T["ndt_options"])

opt_all = ndt_choice == T["ndt_options"][0]
opt_gwt = ndt_choice == T["ndt_options"][1]
opt_ut = ndt_choice == T["ndt_options"][2]
opt_em = ndt_choice == T["ndt_options"][3]

st.sidebar.subheader(T["sb_pipe"])
D_out_inch = st.sidebar.number_input(T["d_out"], value=12.75, step=0.25)
t_nom_mm = st.sidebar.number_input(T["t_nom"], value=9.53, step=0.5)
L_m = st.sidebar.number_input(T["l_m"], value=10.0, step=1.0)

st.sidebar.subheader(T["sb_ndt"])
P_watt = st.sidebar.number_input(T["p_watt"], value=50.0, step=5.0)
Q_base = st.sidebar.number_input(T["q_base"], value=1000.0, step=100.0)

f_gwt_khz = 32.0
f_ut_mhz = 5.0
f_em_ghz = 2.4

if opt_all or opt_gwt:
    f_gwt_khz = st.sidebar.number_input(T["f_gwt"], value=32.0)
if opt_all or opt_ut:
    f_ut_mhz = st.sidebar.number_input(T["f_ut"], value=5.0)
if opt_all or opt_em:
    f_em_ghz = st.sidebar.number_input(T["f_em"], value=2.4)

st.sidebar.subheader(T["sb_op"])
Pg_bar = 50.0
eps_r = 1.05
if opt_all or opt_em:
    Pg_bar = st.sidebar.number_input(T["pg_bar"], value=50.0, step=5.0)
    eps_r = st.sidebar.number_input(T["eps_r"], value=1.05, step=0.01)

defect_pct = st.sidebar.slider(T["defect"], 0, 50, 15)

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

    vcav_g = (np.pi / 4.0) * L_m * (D_out ** 2 - d_in_c ** 2)
    nres_g = vcav_g / V_eq_m3
    nwav_g = (P_watt * q * (lam_gwt ** 2)) / denom_const
    rod_g = nwav_g / nres_g

    vcav_u = (np.pi / 4.0) * (d_p ** 2) * t_c
    nres_u = vcav_u / V_eq_m3
    nwav_u = (P_watt * q * (lam_ut ** 2)) / denom_const
    rod_u = nwav_u / nres_u

    vcav_e = (np.pi / 4.0) * (d_eff_c ** 2) * L_m
    nres_e = vcav_e / V_eq_m3
    nph_e = (P_watt * q * (lam_em ** 2)) / denom_const
    rod_e = nph_e / nres_e
    gdi = 14369.0 / pg_c
    c_idx = rod_e / gdi

    return q, t_c, d_eff_c, rod_g, rod_u, rod_e, c_idx

_, _, _, ROD_gwt_0, ROD_ut_0, ROD_em_0, C_index_0 = calc_metrics(0)
Q_curr, t_curr_gwt, D_eff_em, ROD_gwt, ROD_ut, ROD_em, C_index = calc_metrics(defect_pct)

diff_gwt = ((ROD_gwt - ROD_gwt_0) / ROD_gwt_0) * 100.0
diff_ut = ((ROD_ut - ROD_ut_0) / ROD_ut_0) * 100.0
diff_c = ((C_index - C_index_0) / C_index_0) * 100.0

tab1, tab2, tab3 = st.tabs(T["tabs"])

with tab1:
    st.subheader(f"{T['res_header']} {defect_pct}%")

    if opt_all:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(T["m_gwt"], f"{ROD_gwt:.3e}", f"{diff_gwt:+.2f}%")
            st.caption(f"{T['c_gwt']} {t_curr_gwt*1000:.2f} {T['unit_mm']}")
        with col2:
            st.metric(T["m_ut"], f"{ROD_ut:.3e}", f"{diff_ut:+.2f}%")
            st.caption(f"{T['c_ut']} {Q_curr:.0f}")
        with col3:
            st.metric(T["m_em"], f"{C_index:.3e}", f"{diff_c:+.2f}%")
            st.caption(f"{T['c_em']} {D_eff_em*1000:.1f} {T['unit_mm']}")
    elif opt_gwt:
        st.metric(T["m_gwt"], f"{ROD_gwt:.3e}", f"{diff_gwt:+.2f}%")
        st.caption(f"{T['c_gwt']} {t_curr_gwt*1000:.2f} {T['unit_mm']}")
    elif opt_ut:
        st.metric(T["m_ut"], f"{ROD_ut:.3e}", f"{diff_ut:+.2f}%")
        st.caption(f"{T['c_ut']} {Q_curr:.0f}")
    elif opt_em:
        st.metric(T["m_em"], f"{C_index:.3e}", f"{diff_c:+.2f}%")
        st.caption(f"{T['c_em']} {D_eff_em*1000:.1f} {T['unit_mm']}")

    st.divider()
    st.subheader(T["tbl_header"])
    rows = []
    for s in range(0, 45, 5):
        _, t_c, d_eff_c, rod_g, rod_u, rod_e, c_idx = calc_metrics(s)
        shift_val = ((c_idx - C_index_0) / C_index_0) * 100.0

        row_dict = {}
        if is_ar:
            row_dict["نسبة العيب (%)"] = f"{s}%"
            if opt_all or opt_gwt or opt_ut:
                row_dict["السُمك المتبقي (مم)"] = round(t_c * 1000, 2)
            if opt_all or opt_em:
                row_dict["القطر الفعلي (مم)"] = round(d_eff_c * 1000, 1)
            if opt_all or opt_gwt:
                row_dict["ROD (GWT)"] = f"{rod_g:.3e}"
            if opt_all or opt_ut:
                row_dict["ROD (UT)"] = f"{rod_u:.3e}"
            if opt_all or opt_em:
                row_dict["ROD (EM)"] = f"{rod_e:.3e}"
                row_dict["مؤشر الانسداد C_index"] = f"{c_idx:.3e}"
                row_dict["تغير مؤشر الانسداد"] = f"{shift_val:+.1f}%"
        else:
            row_dict["Defect (%)"] = f"{s}%"
            if opt_all or opt_gwt or opt_ut:
                row_dict["Remaining Wall (mm)"] = round(t_c * 1000, 2)
            if opt_all or opt_em:
                row_dict["Effective ID (mm)"] = round(d_eff_c * 1000, 1)
            if opt_all or opt_gwt:
                row_dict["ROD (GWT)"] = f"{rod_g:.3e}"
            if opt_all or opt_ut:
                row_dict["ROD (UT)"] = f"{rod_u:.3e}"
            if opt_all or opt_em:
                row_dict["ROD (EM)"] = f"{rod_e:.3e}"
                row_dict["C_index"] = f"{c_idx:.3e}"
                row_dict["C_index Shift"] = f"{shift_val:+.1f}%"
        rows.append(row_dict)

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

with tab2:
    st.subheader(T["chart_header"])
    x_vals = list(range(0, 46, 1))
    y_gwt = []
    y_ut = []
    y_c = []
    for s in x_vals:
        _, _, _, rod_g, rod_u, _, c_idx = calc_metrics(s)
        y_gwt.append(round(((rod_g - ROD_gwt_0) / ROD_gwt_0) * 100.0, 2))
        y_ut.append(round(((rod_u - ROD_ut_0) / ROD_ut_0) * 100.0, 2))
