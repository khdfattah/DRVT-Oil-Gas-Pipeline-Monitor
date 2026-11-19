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
    "ndt_select_label": "🔍 اختر نوع الجهاز اللاتلافي (NDT):" if is_ar else "🔍 Select NDT Device Type:",
    "ndt_options": ("الموجات الموجهة (GWT)", "الموجات فوق الصوتية (UT)", "الميكروويف الداخلي (EM)") if is_ar else ("Guided Wave Testing (GWT)", "Ultrasonic Thickness (UT)", "Internal Microwave (EM)"),
    "defect": "نسبة التآكل / الترسبات (%)" if is_ar else "Corrosion / Scaling Ratio (%)",
    "tabs": ("📊 النتائج", "📈 الرسم البياني", "📄 التقرير") if is_ar else ("📊 Results", "📈 Chart", "📄 Report"),
    "res_header": "نتيجة الفحص عند نسبة عيب:" if is_ar else "Inspection Result at Defect Ratio:",
    "m_gwt": "ROD - الموجات الموجهة (GWT)" if is_ar else "ROD - Guided Wave (GWT)",
    "c_gwt": "سُمك الجدار المتبقي:" if is_ar else "Remaining Wall Thickness:",
    "m_ut": "ROD - الموجات فوق الصوتية (UT)" if is_ar else "ROD - Ultrasonic (UT)",
    "c_ut": "معامل الجودة الفعلي Q:" if is_ar else "Effective Quality Factor Q:",
    "m_em": "مؤشر الانسداد (C_index - EM)" if is_ar else "Clogging Index (C_index - EM)",
    "c_em": "القطر الداخلي الفعلي:" if is_ar else "Effective Inner Diameter:",
    "unit_mm": "مم" if is_ar else "mm",
    "tbl_header": "جدول القيم المتدرجة (0% إلى 40%)" if is_ar else "Progressive Values Table (0% to 40%)",
    "chart_header": "منحنى استجابة الجهاز لتفاقم الصدأ والترسبات" if is_ar else "Device Response vs. Corrosion & Scaling Progression",
    "rep_header": "التقرير الفني لحالة الأنبوب" if is_ar else "Technical Pipeline Integrity Report",
    "dl_btn": "📥 تحميل التقرير (.txt)" if is_ar else "📥 Download Report (.txt)",
}

st.title(T["title"])
st.info(T["author_box"])

# الشريط الجانبي: زر اختيار الجهاز فقط + نسبة العيب
ndt_choice = st.sidebar.selectbox(T["ndt_select_label"], T["ndt_options"])
defect_pct = st.sidebar.slider(T["defect"], 0, 50, 15)

opt_gwt = ndt_choice == T["ndt_options"]
opt_ut = ndt_choice == T["ndt_options"]
opt_em = ndt_choice == T["ndt_options"]

# القيم القياسية الثابتة داخلياً (أنبوب 12 بوصة قياسي)
D_out_inch = 12.75
t_nom_mm = 9.53
L_m = 10.0
P_watt = 50.0
Q_base = 1000.0
f_gwt_khz = 32.0
f_ut_mhz = 5.0
f_em_ghz = 2.4
Pg_bar = 50.0
eps_r = 1.05

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
    rod_g = ((P_watt * q * (lam_gwt ** 2)) / denom_const) / (vcav_g / V_eq_m3)

    vcav_u = (np.pi / 4.0) * (d_p ** 2) * t_c
    rod_u = ((P_watt * q * (lam_ut ** 2)) / denom_const) / (vcav_u / V_eq_m3)

    vcav_e = (np.pi / 4.0) * (d_eff_c ** 2) * L_m
    rod_e = ((P_watt * q * (lam_em ** 2)) / denom_const) / (vcav_e / V_eq_m3)
    c_idx = rod_e / (14369.0 / pg_c)

    return q, t_c, d_eff_c, rod_g, rod_u, rod_e, c_idx

_, _, _, ROD_gwt_0, ROD_ut_0, ROD_em_0, C_index_0 = calc_metrics(0)
Q_curr, t_curr_gwt, D_eff_em, ROD_gwt, ROD_ut, ROD_em, C_index = calc_metrics(defect_pct)

diff_gwt = ((ROD_gwt - ROD_gwt_0) / ROD_gwt_0) * 100.0
diff_ut = ((ROD_ut - ROD_ut_0) / ROD_ut_0) * 100.0
diff_c = ((C_index - C_index_0) / C_index_0) * 100.0

tab1, tab2, tab3 = st.tabs(T["tabs"])

with tab1:
    st.subheader(f"{T['res_header']} {defect_pct}%")

    if opt_gwt:
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
            if opt_gwt:
                row_dict["السُمك المتبقي (مم)"] = round(t_c * 1000, 2)
                row_dict["ROD (GWT)"] = f"{rod_g:.3e}"
            elif opt_ut:
                row_dict["السُمك المتبقي (مم)"] = round(t_c * 1000, 2)
                row_dict["ROD (UT)"] = f"{rod_u:.3e}"
            elif opt_em:
                row_dict["القطر الفعلي (مم)"] = round(d_eff_c * 1000, 1)
                row_dict["مؤشر الانسداد C_index"] = f"{c_idx:.3e}"
                row_dict["نسبة التغير"] = f"{shift_val:+.1f}%"
        else:
            row_dict["Defect (%)"] = f"{s}%"
            if opt_gwt:
                row_dict["Remaining Wall (mm)"] = round(t_c * 1000, 2)
                row_dict["ROD (GWT)"] = f"{rod_g:.3e}"
            elif opt_ut:
                row_dict["Remaining Wall (mm)"] = round(t_c * 1000, 2)
                row_dict["ROD (UT)"] = f"{rod_u:.3e}"
            elif opt_em:
                row_dict["Effective ID (mm)"] = round(d_eff_c * 1000, 1)
                row_dict["C_index"] = f"{c_idx:.3e}"
                row_dict["Shift (%)"] = f"{shift_val:+.1f}%"
        rows.append(row_dict)

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

with tab2:
    st.subheader(T["chart_header"])
    x_vals = list(range(0, 46, 1))
    y_vals = []
    for s in x_vals:
        _, _, _, rod_g, rod_u, _, c_idx = calc_metrics(s)
        if opt_gwt:
            y_vals.append(round(((rod_g - ROD_gwt_0) / ROD_gwt_0) * 100.0, 2))
        elif opt_ut:
            y_vals.append(round(((rod_u - ROD_ut_0) / ROD_ut_0) * 100.0, 2))
        elif opt_em:
            y_vals.append(round(((c_idx - C_index_0) / C_index_0) * 100.0, 2))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines+markers", name=ndt_choice))

    x_title = "نسبة التآكل / الترسبات (%)" if is_ar else "Corrosion / Scaling Ratio (%)"
    y_title = "نسبة الانحراف عن الحالة السليمة (%)" if is_ar else "Deviation from Healthy Baseline (%)"
    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        height=420
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader(T["rep_header"])

    if defect_pct < 10:
        status_ar = "حالة سليمة / مستقرة (ضمن الحدود الآمنة)"
        rec_ar = "الاستمرار في المراقبة الدورية المجدولة."
        status_en = "Healthy / Stable Condition (Within safe limits)"
        rec_en = "Continue routine scheduled NDT monitoring."
    elif defect_pct < 25:
        status_ar = "تنبيه مبكر (ترقق ملحوظ في الجدار أو بداية تراكم ترسبات)"
        rec_ar = "جدولة عملية تنظيف للخط (Pigging) وتكثيف الفحص."
        status_en = "Early Warning (Noticeable wall thinning or initial scaling)"
        rec_en = "Schedule pipeline cleaning (Pigging) and increase inspection frequency."
    else:
        status_ar = "حالة حرجة (فقد معدني مرتفع أو تضيق شديد في القطر)"
        rec_ar = "تدخل هندسي عاجل لتخفيض ضغط التشغيل أو استبدال المقطع."
        status_en = "Critical Condition (Severe metal loss or major diameter restriction)"
        rec_en = "Immediate engineering intervention required: reduce pressure or replace section."

    if opt_gwt:
        ind_ar = f"**مؤشر الجهاز (ROD - GWT):** `{ROD_gwt:.3e}` (انحراف: **{diff_gwt:+.2f}%**)"
        ind_en = f"**Device Indicator (ROD - GWT):** `{ROD_gwt:.3e}` (Shift: **{diff_gwt:+.2f}%**)"
    elif opt_ut:
        ind_ar = f"**مؤشر الجهاز (ROD - UT):** `{ROD_ut:.3e}` (انحراف: **{diff_ut:+.2f}%**)"
        ind_en = f"**Device Indicator (ROD - UT):** `{ROD_ut:.3e}` (Shift: **{diff_ut:+.2f}%**)"
    else:
        ind_ar = f"**مؤشر الجهاز (C_index - EM):** `{C_index:.3e}` (انحراف: **{diff_c:+.2f}%**)"
        ind_en = f"**Device Indicator (C_index - EM):** `{C_index:.3e}` (Shift: **{diff_c:+.2f}%**)"

    if is_ar:
        report_text = f"""### تقرير فني: تقييم سلامة الأنابيب وفق نظرية الحجم الرنيني الديناميكي (DRVT)
**إعداد:** د. خالد عبدالفتاح محمد عثمان — معهد مروي التكنولوجي، جامعة مروي التكنولوجية، السودان  
**الجهاز اللاتلافي المستخدم:** {ndt_choice}

---

* **نسبة العيب / الترسبات المرصودة:** {defect_pct}%
* **التقييم العام للحالة:** {status_ar}
* {ind_ar}
* **التوصية الهندسية:** {rec_ar}
"""
    else:
        report_text = f"""### Technical Report: Pipeline Integrity Assessment via DRVT
**Author:** Dr. Khalid Abdel Fattah Mohamed Osman — Merowe Institute of Technology, Merowe University of Technology, Sudan  
**NDT Device Used:** {ndt_choice}

---

* **Detected Defect / Scaling Ratio:** {defect_pct}%
* **Overall Condition Status:** {status_en}
* {ind_en}
* **Engineering Recommendation:** {rec_en}
"""

