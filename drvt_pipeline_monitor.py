import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime

# ==========================================
# 1. إعداد الصفحة والقاموس الثنائي اللغة
# ==========================================
st.set_page_config(
    page_title="DRVT Oil & Gas Pipeline Monitor",
    page_icon="🔬",
    layout="wide"
)

TEXT = {
    "ar": {
        "title": "🔬 DRVT Oil & Gas Pipeline Monitor",
        "author_line": "**المؤلف:** د. خالد عبدالفتاح محمد عثمان | معهد مروي التكنولوجي، جامعة مروي التكنولوجية، السودان",
        "subtitle": "منصة تحليل موحدة فوق أجهزة الفحص غير المتلف (NDT) لتحويل القراءات إلى قرارات سلامة وصيانة",
        "lang_btn": "🌐 English",
        "tab_results": "📊 النتائج والقرارات (Results & Decisions)",
        "tab_chart": "📈 الرسم البياني (Chart)",
        "tab_report": "📄 التقرير الفني (Technical Report)",
        "sidebar_header": "⚙️ إعدادات الفحص والتشغيل",
        "method_label": "اختر تقنية الفحص (NDT Method)",
        "mode_label": "طبيعة الظاهرة المرصودة",
        "modes": ["تآكل وترقق الجدار (Corrosion)", "ترسبات وانسداد داخلي (Scaling / Fouling)"],
        "show_physics": "🔬 إظهار الحسابات الرنينية المتقدمة (DRVT Physics)",
        "pipe_params": "📏 الأبعاد المرجعية للأنبوب",
        "d_out": "القطر الخارجي الأصلي D_out (mm)",
        "t_orig": "سُمك الجدار الأصلي t_0 (mm)",
        "d_crit": "القطر الفعال الحرج D_critical (mm)",
        "years": "زمن التشغيل منذ الفحص المرجعي (سنوات)",
        "device_inputs": "📡 مدخلات جهاز الفحص",
        "exec_header": "📊 مؤشرات القرار التنفيذية لمهندس السلامة",
        "phi": "مؤشر صحة الأنبوب (PHI)",
        "deff": "القطر الداخلي الفعال (D_eff)",
        "rate": "معدل التآكل / الترسيب",
        "rul": "العمر التشغيلي المتبقي (RUL)",
        "risk_header": "🚨 تقييم الخطورة وتوصية الصيانة",
        "risk_level": "مستوى الخطورة",
        "recommendation": "توصية الصيانة والتشغيل",
        "physics_header": "⚛️ المحرك الفيزيائي الرنيني (DRVT Internal Calculations)",
        "physics_note": "تُحسب هذه القيم في الخلفية لتوحيد قراءات أجهزة الفحص المختلفة وتحويلها إلى D_eff:",
        "unit_year": "سنة",
        "unit_rate": "mm/سنة",
        "infinite": "مستقر (> 50 سنة)",
        "chart_title": "تطور القطر الفعال (D_eff) مقارنة بالحد الحرج (D_critical) عبر الزمن",
        "chart_x": "الزمن (سنوات)",
        "chart_y": "القطر (mm)",
        "report_title": "ملخص التقرير الفني لسلامة خط الأنابيب",
        "dl_pdf": "📥 تحميل التقرير الفني (PDF)",
        "dl_csv": "📊 تحميل بيانات الفحص (CSV)",
        "risk_high": "🔴 خطر مرتفع (High Risk)",
        "risk_sched": "🟠 صيانة مجدولة (Scheduled Maintenance)",
        "risk_mon": "🟡 مراقبة (Monitoring)",
        "risk_opt": "🟢 ممتاز (Optimal)",
        "act_high": "خفض ضغط التشغيل فوراً أو إيقاف الخط لإجراء فحص تفصيلي وتدخل عاجل.",
        "act_sched_scale": "جدولة عملية تنظيف ميكانيكي أو كيميائي (Pigging / Cleaning) خلال 3 إلى 6 أشهر.",
        "act_sched_corr": "جدولة فحص NDT موسّع وتجهيز خطة تدعيم أو استبدال وقائي خلال 6 أشهر.",
        "act_mon": "مراقبة دورية كل 6 إلى 12 شهراً ومتابعة تغير معدل التآكل/الترسيب.",
        "act_opt": "الخط في حالة ممتازة؛ استمرار التشغيل وفق جدول الفحص الاعتيادي."
    },
    "en": {
        "title": "🔬 DRVT Oil & Gas Pipeline Monitor",
        "author_line": "**Author:** Dr. Khalid Abdel Fattah Mohamed Osman | Merowe Institute of Technology, Merowe University of Technology, Sudan",
        "subtitle": "Unified Analysis Layer over NDT Devices for Actionable Integrity & Maintenance Decisions",
        "lang_btn": "🌐 العربية",
        "tab_results": "📊 Results & Decisions",
        "tab_chart": "📈 Chart",
        "tab_report": "📄 Technical Report",
        "sidebar_header": "⚙️ Inspection & Operating Setup",
        "method_label": "Select Inspection Method (NDT)",
        "mode_label": "Observed Degradation Mechanism",
        "modes": ["Wall Corrosion / Thinning", "Internal Scaling / Fouling"],
        "show_physics": "🔬 Show Advanced DRVT Resonant Calculations",
        "pipe_params": "📏 Reference Pipe Geometry",
        "d_out": "Original Outer Diameter D_out (mm)",
        "t_orig": "Original Wall Thickness t_0 (mm)",
        "d_crit": "Critical Effective Diameter D_critical (mm)",
        "years": "Operating Time Since Baseline (years)",
        "device_inputs": "📡 NDT Sensor Inputs",
        "exec_header": "📊 Executive Decision Indicators (Safety Engineer View)",
        "phi": "Pipeline Health Index (PHI)",
        "deff": "Current Effective Diameter (D_eff)",
        "rate": "Corrosion / Scaling Rate",
        "rul": "Remaining Useful Life (RUL)",
        "risk_header": "🚨 Risk Assessment & Maintenance Recommendation",
        "risk_level": "Risk Level",
        "recommendation": "Maintenance Recommendation",
        "physics_header": "⚛️ DRVT Resonant Physics Engine (Internal Layer)",
        "physics_note": "Computed in the backend to normalize raw NDT signals into D_eff:",
        "unit_year": "years",
        "unit_rate": "mm/year",
        "infinite": "Stable (> 50 years)",
        "chart_title": "Effective Diameter (D_eff) Trajectory vs. Critical Limit (D_critical)",
        "chart_x": "Time (years)",
        "chart_y": "Diameter (mm)",
        "report_title": "Pipeline Integrity Technical Report Summary",
        "dl_pdf": "📥 Download Technical Report (PDF)",
        "dl_csv": "📊 Download Inspection Data (CSV)",
        "risk_high": "🔴 High Risk",
        "risk_sched": "🟠 Scheduled Maintenance",
        "risk_mon": "🟡 Monitoring",
        "risk_opt": "🟢 Optimal",
        "act_high": "Derate operating pressure immediately or shut in line for urgent detailed inspection.",
        "act_sched_scale": "Schedule mechanical/chemical cleaning (Pigging) within 3–6 months.",
        "act_sched_corr": "Schedule expanded NDT inspection and preventive repair/sleeve within 6 months.",
        "act_mon": "Routine monitoring every 6–12 months and track degradation rate trend.",
        "act_opt": "Pipeline is in optimal condition; continue normal operating & inspection schedule."
    }
}

if "lang" not in st.session_state:
    st.session_state.lang = "en"

def toggle_lang():
    st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"

L = TEXT[st.session_state.lang]
direction = "rtl" if st.session_state.lang == "ar" else "ltr"

st.markdown(
    f"""
    <style>
    .main, .stSidebar {{ direction: {direction}; text-align: {'right' if direction=='rtl' else 'left'}; }}
    .author-box {{
        background-color: #f4f6f9;
        padding: 12px 16px;
        border-radius: 8px;
        border-{'right' if direction=='rtl' else 'left'}: 4px solid #1f77b4;
        margin-bottom: 12px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. الشريط العلوي (العنوان، المؤلف، وزر تبديل اللغة)
# ==========================================
col_title, col_lang = st.columns([5, 1])
with col_title:
    st.title(L["title"])
    st.caption(L["subtitle"])
with col_lang:
    st.write("")
    st.button(L["lang_btn"], on_click=toggle_lang, use_container_width=True)

st.markdown(f'<div class="author-box">{L["author_line"]}</div>', unsafe_allow_html=True)

# ==========================================
# 3. الشريط الجانبي (الأجهزة، الأبعاد، وزر الحسابات الرنينية)
# ==========================================
with st.sidebar:
    st.header(L["sidebar_header"])

    show_physics = st.toggle(L["show_physics"], value=False)

    devices = [
        "Ultrasonic (UT)",
        "Guided Wave (GWT)",
        "Microwave / Cavity NDT",
        "PAUT",
        "Eddy Current",
        "Radiography"
    ]
    device = st.radio(L["method_label"], devices)

    mode = st.selectbox(L["mode_label"], L["modes"])
    is_scaling = (mode == L["modes"][1])

    st.subheader(L["pipe_params"])
    d_out = st.number_input(L["d_out"], min_value=10.0, value=114.3, step=1.0)
    t_orig = st.number_input(L["t_orig"], min_value=1.0, value=7.15, step=0.1)
    d0 = d_out - 2 * t_orig
    d_crit = st.number_input(L["d_crit"], min_value=5.0, value=round(d0 * 0.70, 1), step=1.0)
    years = st.number_input(L["years"], min_value=0.1, value=3.0, step=0.5)

    st.subheader(L["device_inputs"])

    V_eq = 286.398e-27
    h = 6.6261e-34
    c = 299792458.0
    v_s = 5900.0
    P_power = 0.05
    Q_factor = 1200.0
    P_g = 2.5e6

    rod_val = 0.0
    n_res_val = 0.0
    gdi_val = 14369.0 / P_g
    c_index_val = None

    if device in ["Ultrasonic (UT)", "PAUT"]:
        t_meas = st.number_input("Measured Wall Thickness t (mm)", min_value=0.5, value=5.5, step=0.1)
        freq_mhz = st.number_input("Probe Frequency f (MHz)", min_value=0.5, value=5.0, step=0.5)
        d_probe = st.number_input("Probe Diameter d_p (mm)", min_value=2.0, value=10.0, step=1.0)

        if is_scaling:
            scale_thick = st.number_input("Measured Deposit Thickness (mm)", min_value=0.0, value=3.0, step=0.2)
            deff = max(d0 - 2 * scale_thick, 1.0)
        else:
            wall_loss = max(t_orig - t_meas, 0.0)
            deff = max(d0 - 2 * wall_loss, 1.0)

        t_m = t_meas * 1e-3
        dp_m = d_probe * 1e-3
        f_hz = freq_mhz * 1e6
        v_cav = (math.pi * (dp_m ** 2) / 4.0) * t_m
        n_res_val = v_cav / V_eq
        rod_val = (4 * V_eq * P_power * Q_factor * (v_s ** 2)) / (
            2 * (math.pi ** 2) * h * (c ** 2) * (dp_m ** 2) * t_m * (f_hz ** 2)
        )

    elif device == "Guided Wave (GWT)":
        area_loss_pct = st.slider("Cross-Sectional Metal Loss (%)", 0.0, 60.0, 12.0, 0.5)
        length_m = st.number_input("Inspected Section Length L (m)", min_value=1.0, value=10.0, step=1.0)
        freq_khz = st.number_input("Guided Wave Frequency f (kHz)", min_value=10.0, value=50.0, step=5.0)

        orig_metal_area = (math.pi / 4.0) * (d_out ** 2 - d0 ** 2)
        rem_metal_area = orig_metal_area * (1.0 - area_loss_pct / 100.0)
        d_in_new = math.sqrt(max(d_out ** 2 - (4.0 * rem_metal_area / math.pi), 1.0))
        wall_loss = max((d_in_new - d0) / 2.0, 0.0)
        deff = max(d0 - 2 * wall_loss, 1.0)

        v_wall = (math.pi / 4.0) * ((d_out * 1e-3) ** 2 - (d_in_new * 1e-3) ** 2) * length_m
        n_res_val = v_wall / V_eq
        n_waves = (P_power * Q_factor * (v_s ** 2)) / (2 * math.pi * h * (c ** 2) * ((freq_khz * 1e3) ** 2))
        rod_val = n_waves / n_res_val

    elif device == "Microwave / Cavity NDT":
        deff = st.number_input("Measured Cavity Effective Diameter D_eff (mm)", min_value=5.0, value=round(d0 * 0.90, 1), step=0.5)
        freq_ghz = st.number_input("Resonant Frequency f (GHz)", min_value=0.5, value=2.45, step=0.1)
        eps_r = st.number_input("Fluid Dielectric Constant ε_r", min_value=1.0, value=2.1, step=0.1)
        p_bar = st.number_input("Line Gas/Fluid Pressure (bar)", min_value=1.0, value=25.0, step=1.0)
        P_g = p_bar * 1e5
        gdi_val = 14369.0 / P_g

        deff_m = deff * 1e-3
        f_hz = freq_ghz * 1e9
        v_cav = (math.pi * (deff_m ** 2) * 1.0) / 4.0
        n_res_val = v_cav / V_eq
        rod_val = (2 * V_eq * P_power * Q_factor) / (
            (math.pi ** 2) * h * (f_hz ** 2) * eps_r * (deff_m ** 2) * 1.0
        )
        c_index_val = rod_val / gdi_val

    else:  # Eddy Current / Radiography
        loss_input = st.number_input("Measured Radial Defect / Deposit Depth (mm)", min_value=0.0, value=2.5, step=0.1)
        deff = max(d0 - 2 * loss_input, 1.0)
        v_cav = (math.pi * ((deff * 1e-3) ** 2) * 1.0) / 4.0
        n_res_val = v_cav / V_eq
        rod_val = 7.02e-9 * (d0 / deff) ** 2

# ==========================================
# 4. الحسابات التنفيذية الموحدة
# ==========================================
phi = min(max((deff / d0) * 100.0, 0.0), 100.0)
loss_mm = max(d0 - deff, 0.0)
rate = loss_mm / years
rul = max((deff - d_crit) / rate, 0.0) if rate > 0 else 999.0

if phi < 70.0 or rul < 1.5:
    risk_text = L["risk_high"]
    risk_en = "High Risk"
    action_text = L["act_high"]
    action_en = TEXT["en"]["act_high"]
    alert_type = "error"
elif phi < 85.0 or rul < 4.0:
    risk_text = L["risk_sched"]
    risk_en = "Scheduled Maintenance"
    action_text = L["act_sched_scale"] if is_scaling else L["act_sched_corr"]
    action_en = TEXT["en"]["act_sched_scale"] if is_scaling else TEXT["en"]["act_sched_corr"]
    alert_type = "warning"
elif phi < 95.0:
    risk_text = L["risk_mon"]
    risk_en = "Monitoring"
    action_text = L["act_mon"]
    action_en = TEXT["en"]["act_mon"]
    alert_type = "info"
else:
    risk_text = L["risk_opt"]
    risk_en = "Optimal"
    action_text = L["act_opt"]
    action_en = TEXT["en"]["act_opt"]
    alert_type = "success"

# ==========================================
# 5. دالة توليد ملف PDF احترافي للتقرير الفني
# ==========================================
def build_pdf_report() -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ترويسة التقرير
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "DRVT Oil & Gas Pipeline Monitor - Technical Report", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(0, 6, "Author: Dr. Khalid Abdel Fattah Mohamed Osman", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Affiliation: Merowe Institute of Technology, Merowe University of Technology, Sudan", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # خط فاصل
    pdf.set_draw_color(31, 119, 180)
    pdf.set_line_width(0.6)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # قسم المؤشرات التنفيذية
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "1. Executive Integrity & Decision Summary", new_x="LMARGIN", new_y="NEXT")

    rows = [
        ("Inspection Method (NDT)", device),
        ("Degradation Mechanism", "Internal Scaling / Fouling" if is_scaling else "Wall Corrosion / Thinning"),
        ("Original Outer Diameter (D_out)", f"{d_out:.2f} mm"),
        ("Baseline Inner Diameter (D_0)", f"{d0:.2f} mm"),
        ("Current Effective Diameter (D_eff)", f"{deff:.2f} mm"),
        ("Critical Effective Diameter (D_crit)", f"{d_crit:.2f} mm"),
        ("Pipeline Health Index (PHI)", f"{phi:.1f} %"),
        ("Degradation Rate", f"{rate:.2f} mm/year"),
        ("Remaining Useful Life (RUL)", f"{rul:.1f} years" if rul < 50 else "Stable (> 50 years)"),
        ("Risk Classification", risk_en),
    ]

    pdf.set_font("Helvetica", "", 10)
    for label, val in rows:
        pdf.set_fill_color(245, 247, 250)
        pdf.cell(95, 8, f"  {label}", border=1, fill=True)
        pdf.cell(95, 8, f"  {val}", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "2. Maintenance & Operational Recommendation", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 7, action_en, border=1)

    if show_physics:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "3. DRVT Resonant Physics Parameters (Backend Engine)", new_x="LMARGIN", new_y="NEXT")
        phys_rows = [
            ("Reference Resonant Volume (V_eq)", "286.398 nm^3"),
            ("Resonant Storage Capacity (N_res)", f"{n_res_val:.4e}"),
            ("Resonant Occupancy Density (ROD)", f"{rod_val:.4e}"),
            ("Gas Dissipation Index (GDI)", f"{gdi_val:.4e}"),
        ]
        if c_index_val is not None:
            phys_rows.append(("Total Clogging Index (C_index)", f"{c_index_val:.4e}"))

        pdf.set_font("Helvetica", "", 10)
        for label, val in phys_rows:
            pdf.cell(95, 8, f"  {label}", border=1, fill=True)
            pdf.cell(95, 8, f"  {val}", border=1, new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())

# ==========================================
# 6. التبويبات الرئيسية (Results & Decisions | Chart | Technical Report)
# ==========================================
tab1, tab2, tab3 = st.tabs([L["tab_results"], L["tab_chart"], L["tab_report"]])

with tab1:
    st.subheader(f"{L['exec_header']} — [{device}]")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(L["phi"], f"{phi:.1f}%", delta=f"{phi - 100.0:.1f}%" if phi < 100 else "0.0%")
    c2.metric(L["deff"], f"{deff:.1f} mm", delta=f"-{loss_mm:.2f} mm" if loss_mm > 0 else "0.0 mm")
    c3.metric(L["rate"], f"{rate:.2f} {L['unit_rate']}")
    c4.metric(L["rul"], f"{rul:.1f} {L['unit_year']}" if rul < 50 else L["infinite"])

    st.progress(int(phi))

    st.subheader(L["risk_header"])
    msg = f"**{L['risk_level']}:** {risk_text}\n\n**{L['recommendation']}:** {action_text}"
    if alert_type == "error":
        st.error(msg)
    elif alert_type == "warning":
        st.warning(msg)
    elif alert_type == "info":
        st.info(msg)
    else:
        st.success(msg)

    if show_physics:
        st.divider()
        st.subheader(L["physics_header"])
        st.caption(L["physics_note"])
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Resonant Storage (N_res)", f"{n_res_val:.3e}")
        p2.metric("Occupancy Density (ROD)", f"{rod_val:.3e}")
        p3.metric("Gas Dissipation (GDI)", f"{gdi_val:.3e}")
        if c_index_val is not None:
            p4.metric("Clogging Index (C_index)", f"{c_index_val:.3e}")
        else:
            p4.metric("Baseline Inner D_0", f"{d0:.1f} mm")

with tab2:
    st.subheader(L["chart_title"])
    horizon = max(years + (rul if rul < 25 else 10.0), 5.0)
    t_points = [round(i * horizon / 20.0, 2) for i in range(21)]
    d_points = [max(d0 - rate * t, 0.0) for t in t_points]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t_points, y=d_points, mode="lines+markers", name="D_eff"))
    fig.add_trace(go.Scatter(
        x=[0, horizon], y=[d_crit, d_crit],
        mode="lines", name="D_critical", line=dict(dash="dash", color="red")
    ))
    fig.update_layout(xaxis_title=L["chart_x"], yaxis_title=L["chart_y"])
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader(L["report_title"])
    st.markdown(L["author_line"])

    report_rows = [
        ("NDT Method", device),
        ("Mechanism", mode),
        ("Baseline Inner Diameter D_0 (mm)", f"{d0:.2f}"),
        ("Effective Diameter D_eff (mm)", f"{deff:.2f}"),
        ("Critical Diameter D_critical (mm)", f"{d_crit:.2f}"),
        ("Pipeline Health Index (PHI %)", f"{phi:.1f}%"),
        ("Degradation Rate (mm/year)", f"{rate:.2f}"),
        ("Remaining Useful Life (RUL)", f"{rul:.1f} years" if rul < 50 else "> 50 years"),
        ("Risk Level", risk_text),
        ("Maintenance Recommendation", action_text),
    ]

    if show_physics:
        report_rows.extend([
            ("Resonant Storage (N_res)", f"{n_res_val:.4e}"),
            ("Resonant Occupancy Density (ROD)", f"{rod_val:.4e}"),
            ("Gas Dissipation Index (GDI)", f"{gdi_val:.4e}"),
        ])
        if c_index_val is not None:
            report_rows.append(("Clogging Index (C_index)", f"{c_index_val:.4e}"))

    report_df = pd.DataFrame(report_rows, columns=["Parameter", "Value"])
    st.table(report_df)

    # أزرار التصدير المباشر (PDF و CSV)
    dl1, dl2 = st.columns(2)
    with dl1:
        pdf_bytes = build_pdf_report()
        st.download_button(
            label=L["dl_pdf"],
            data=pdf_bytes,
            file_name=f"DRVT_Pipeline_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with dl2:
        csv_bytes = report_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label=L["dl_csv"],
            data=csv_bytes,
            file_name=f"DRVT_Pipeline_Data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
