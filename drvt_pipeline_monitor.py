def build_pdf_report():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    epw = max(pdf.w - pdf.l_margin - pdf.r_margin, 50.0)

    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    unicode_font = next((p for p in font_candidates if os.path.exists(p)), None)

    if unicode_font:
        pdf.add_font("CustomFont", "", unicode_font)
        pdf.set_font("CustomFont", size=14)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(epw, 10, "DRVT Pipeline Integrity Technical Report")
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
            lines.append(
                f"DRVT Resonant Metrics (Research): ROD_GWT={rod_g_now:.4e} ({diff_g:+.2f}%), "
                f"ROD_UT={rod_u_now:.4e} ({diff_u:+.2f}%), C_index={c_idx_now:.4e} ({diff_c:+.2f}%)"
            )
        lines.append(
            "Note: DRVT in NDT is a theoretical/extrapolative model requiring experimental calibration "
            "and does not replace engineering codes or minimum wall calculations."
        )
        for line in lines:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(epw, 7, str(line))
    else:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(epw, 10, "DRVT Pipeline Integrity Technical Report")
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
            clean_line = str(line).encode("latin-1", errors="replace").decode("latin-1")
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(epw, 7, clean_line)

    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")
