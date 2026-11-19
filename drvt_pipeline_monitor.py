import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="DRVT - NDT Pipeline Monitor", layout="wide")

# زر اختيار اللغة
lang = st.sidebar.radio(
    "🌐 Language / اللغة", ("العربية", "English"), horizontal=True
)
is_ar = lang == "العربية"

# ضبط اتجاه الصفحة
if is_ar:
  st.markdown(
      "<style>.main, .stSidebar { direction: rtl; text-align: right; } h1, h2,"
      " h3, p, div, label { text-align: right; }</style>",
      unsafe_allow_html=True,
  )
else:
  st.markdown(
      "<style>.main, .stSidebar { direction: ltr; text-align: left; } h1, h2,"
      " h3, p, div, label { text-align: left; }</style>",
      unsafe_allow_html=True,
  )

# قاموس النصوص
T = {
    "title": (
        "🔬 نظام مراقبة سلامة الأنابيب بنظرية الحجم الرنيني الديناميكي (DRVT)"
        if is_ar
        else "🔬 DRVT Pipeline Integrity Monitoring System (NDT)"
    ),
    "author_box": (
        "**إعداد وتطوير:** د. خالد عبدالفتاح محمد عثمان | معهد مروي التكنولوجي،"
        " جامعة مروي التكنولوجية، السودان (`khdfattah@gmail.com`)"
        if is_ar
        else (
            "**Author:** Dr. Khalid Abdel Fattah Mohamed Osman | Merowe"
            " Institute of Technology, Merowe University of Technology, Sudan"
            " (`khdfattah@gmail.com`)"
        )
    ),
    "sb_header": (
        "⚙️ إعدادات الفحص والأنبوب"
        if is_ar
        else "⚙️ Inspection & Pipeline Settings"
    ),
    "ndt_select_label": (
        "🔍 اختر تقنية الفحص (NDT):"
        if is_ar
        else "🔍 Select NDT Inspection Method:"
    ),
    "ndt_options": (
        (
            "الكل (مقارنة شاملة)",
            "الموجات الموجهة (GWT)",
            "الموجات فوق الصوتية (UT)",
            "الميكروويف الداخلي (EM)",
        )
        if is_ar
        else (
            "All Methods (Comparison)",
            "Guided Wave Testing (GWT)",
            "Ultrasonic Thickness (UT)",
            "Internal Microwave (EM)",
        )
    ),
    "sb_pipe": (
        "1. أبعاد الأنبوب القياسي"
        if is_ar
        else "1. Standard Pipeline Dimensions"
    ),
    "d_out": (
        "القطر الخارجي (بوصة)" if is_ar else "Outer Diameter D_out (inches)"
    ),
    "t_nom": (
        "سُمك الجدار الاسمي (مم)" if is_ar else "Nominal Wall Thickness t (mm)"
    ),
    "l_m": (
        "طول المقطع المفحوص (متر)" if is_ar else "Inspected Section Length L (m)"
    ),
    "sb_ndt": "2. معاملات جهاز الفحص" if is_ar else "2. NDT Device Parameters",
    "p_watt": "قدرة الإرسال P (واط)" if is_ar else "Transmitted Power P (W)",
    "q_base": (
        "معامل الجودة المرجعي Q₀" if is_ar else "Baseline Quality Factor Q₀"
    ),
    "f_gwt": (
        "تردد الموجات الموجهة GWT (كيلوهرتز)"
        if is_ar
        else "Guided Wave Frequency GWT (kHz)"
    ),
    "f_ut": (
        "تردد الموجات فوق الصوتية UT (ميجاهرتز)"
        if is_ar
        else "Ultrasonic Frequency UT (MHz)"
    ),
    "f_em": (
        "تردد الميكروويف EM (جيجاهرتز)"
        if is_ar
        else "Microwave Frequency EM (GHz)"
    ),
    "sb_op": (
        "3. ظروف التشغيل والعيوب"
        if is_ar
        else "3. Operating Conditions & Defects"
    ),
    "pg_bar": "ضغط الغاز الطبيعي (بار)" if is_ar else "Gas Pressure Pg (bar)",
    "eps_r": (
        "ثابت العزل للغاز εr" if is_ar else "Relative Permittivity εr"
    ),
    "defect": (
        "نسبة التآكل / الترسبات المستهدفة (%)"
        if is_ar
        else "Target Corrosion / Scaling Ratio (%)"
    ),
    "tabs": (
        (
            "📊 لوحة المحاكاة والنتائج",
            "📈 الرسوم البيانية",
            "📄 التقرير الفني",
        )
        if is_ar
        else (
            "📊 Simulation Dashboard",
            "📈 Response Charts",
            "📄 Technical Report",
        )
    ),
    "res_header": (
        "نتائج الفحص عند نسبة تآكل / ترسبات:"
        if is_ar
        else "Inspection Results at Defect Ratio:"
    ),
    "m_gwt": "ROD - الموجات الموجهة (GWT)" if is_ar else "ROD - Guided Wave (GWT)",
    "c_gwt": (
        "سُمك الجدار المتبقي:" if is_ar else "Remaining Wall Thickness:"
    ),
    "m_ut": (
        "ROD - الموجات فوق الصوتية (UT)" if is_ar else "ROD - Ultrasonic (UT)"
    ),
    "c_ut": "معامل الجودة الفعلي Q:" if is_ar else "Effective Quality Factor Q:",
    "m_em": (
        "مؤشر الانسداد (C_index - EM)"
        if is_ar
        else "Clogging Index (C_index - EM)"
    ),
    "c_em": (
        "القطر الداخلي الفعلي:" if is_ar else "Effective Inner Diameter:"
    ),
    "unit_mm": "مم" if is_ar else "mm",
    "tbl_header": (
        "جدول مقارنة السيناريوهات المتدرجة (0% إلى 40%)"
        if is_ar
        else "Progressive Defect Scenarios Table (0% to 40%)"
    ),
    "chart_header": (
        "منحنى استجابة مؤشرات DRVT لتفاقم الصدأ والترسبات"
        if is_ar
        else "DRVT Indicators Response vs. Corrosion & Scaling Progression"
    ),
    "rep_header": (
        "التقرير الفني لحالة مراقبة الأنابيب"
        if is_ar
        else "Technical Pipeline Integrity Report"
    ),
    "dl_btn": (
        "📥 تحميل التقرير الفني (ملف نصي)"
        if is_ar
        else "📥 Download Technical Report (.txt)"
    ),
}

st.title(T["title"])
st.info(T["author_box"])

# الشريط الجانبي
st.sidebar.header(T["sb_header"])
ndt_choice = st.sidebar.selectbox(T["ndt_select_label"], T["ndt_options"])

# تحديد الخيار المختار برمجياً
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

# الثوابت الفيزيائية
V_eq_nm3 = 286.398
V_eq_m3 = V_eq_nm3 * 1e-27
h = 6.6261e-34
c = 299792458.0
v_s = 5900.0
d_p = 0.0127

D_out = D_out_inch * 0.0254
t_nom = t_nom_mm / 1000.0
D_in = D_out - 2 * t_nom
Pg_pa = Pg_bar * 100000.0

# الحسابات الأساسية
ratio = defect_pct / 100.0
Q_curr = Q_base * (1 - 0.5 * ratio)

# 1. GWT
t_curr_gwt = t_nom * (1 - ratio)
D_in_curr_gwt = D_out - 2 * t_curr_gwt
V_cav_gwt = (np.pi / 4) * L_m * (D_out**2 - D_in_curr_gwt**2)
N_res_gwt = V_cav_gwt / V_eq_m3
lam_gwt = v_s / (f_gwt_khz * 1000)
N_wav_gwt = (P_watt * Q_curr * (lam_gwt**2)) / (2 * np.pi * h * (c**2))
ROD_gwt = N_wav_gwt / N_res_gwt

V_cav_gwt_0 = (np.pi / 4) * L_m * (D_out**2 - D_in**2)
N_wav_gwt_0 = (P_watt * Q_base * (lam_gwt**2)) / (2 * np.pi * h * (c**2))
ROD_gwt_0 = N_wav_gwt_0 / (V_cav_gwt_0 / V_eq_m3)
diff_gwt = ((ROD_gwt - ROD_gwt_0) / ROD_gwt_0) * 100

# 2. UT
V_cav_ut = (np.pi / 4) * (d_p**2) * t_curr_gwt
N_res_ut = V_cav_ut / V_eq_m3
lam_ut = v_s / (f_ut_mhz * 1e6)
N_wav_ut = (P_watt * Q_curr * (lam_ut**2)) / (2 * np.pi * h * (c**2))
ROD_ut = N_wav_ut / N_res_ut

V_cav_ut_0 = (np.pi / 4) * (d_p**2) * t_nom
N_wav_ut_0 = (P_watt * Q_base * (lam_ut**2)) / (2 * np.pi * h * (c**2))
ROD_ut_0 = N_wav_ut_0 / (V_cav_ut_0 / V_eq_m3)
diff_ut = ((ROD_ut - ROD_ut_0) / ROD_ut_0) * 100

# 3. EM
D_eff_em = D_in * (1 - ratio)
Pg_curr = Pg_pa * (1 + 0.4 * ratio)
V_cav_em = (np.pi / 4) * (D_eff_em**2) * L_m
N_res_em = V_cav_em / V_eq_m3
lam_em = c / ((f_em_ghz * 1e9) * np.sqrt(eps_r))
N_ph_em = (P_watt * Q_curr * (lam_em**2)) / (2 * np.pi * h * (c**2))
ROD_em = N_ph_em / N_res_em
GDI_curr = 14369.0 / Pg_curr
C_index = ROD_em / GDI_curr

V_cav_em_0 = (np.pi / 4) * (D_in**2) * L_m
N_ph_em_0 = (P_watt * Q_base * (lam_em**2)) / (2 * np.pi * h * (c**2))
ROD_em_0 = N_ph_em_0 / (V_cav_em_0 / V_eq_m3)
C_index_0 = ROD_em_0 / (14369.0 / Pg_pa)
diff_c = ((C_index - C_index_0) / C_index_0) * 100

# التبويبات
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
  scenarios = tuple(range(0, 45, 5))
  rows = []
  for s in scenarios:
    r = s / 100.0
    q = Q_base * (1 - 0.5 * r)
    t_c = t_nom * (1 - r)
    d_in_c = D_out - 2 * t_c
    d_eff_c = D_in * (1 - r)
    pg_c = Pg_pa * (1 + 0.4 * r)

    rod_g = ((P_watt * q * (lam_gwt**2)) / (2 * np.pi * h * (c**2))) / (
        ((np.pi / 4) * L_m * (D_out**2 - d_in_c**2)) / V_eq_m3
    )
    rod_u = ((P_watt * q * (lam_ut**2)) / (2 * np.pi * h * (c**2))) / (
