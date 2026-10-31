import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Adds 'Page X of Y' and confidential project footer to every page."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        # Top rule for footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 35, 572, 35)
        
        footer_text = "ImageSentinel - OSINT Image Privacy & Metadata Analysis System"
        self.drawString(40, 24, footer_text)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 24, page_str)
        self.restoreState()


class PDFReportGenerator:
    """Generates professional OSINT Image Privacy Reports using ReportLab."""

    @classmethod
    def generate(cls, metadata, risk, visual_results=None, comp_results=None, output_path="reports/report.pdf"):
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=50
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a")
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#0284c7")
        )
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'BodyDark',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#334155")
        )
        cell_bold = ParagraphStyle(
            'CellBold',
            parent=body_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#0f172a")
        )
        callout_text = ParagraphStyle(
            'CalloutText',
            parent=body_style,
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#b91c1c")
        )

        story = []

        # --- Header Banner ---
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header_data = [
            [
                Paragraph("<b>IMAGESENTINEL</b><br/><font size=8 color='#64748b'>LOCAL OSINT PRIVACY AUDIT</font>", title_style),
                Paragraph(f"<b>REPORT GENERATED:</b><br/>{now_str}", ParagraphStyle('RightTime', parent=body_style, alignment=2))
            ]
        ]
        t_header = Table(header_data, colWidths=[330, 202])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_header)
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10, spaceBefore=4))

        # --- Section 1: Image Summary ---
        story.append(Paragraph("1. IMAGE SUMMARY & INTEGRITY", section_style))
        file_info = metadata.get("file_info", {})
        basic = metadata.get("basic_info", {})
        
        sum_data = [
            [Paragraph("<b>Filename:</b>", cell_bold), Paragraph(str(file_info.get("filename", "N/A")), body_style),
             Paragraph("<b>Format / MIME:</b>", cell_bold), Paragraph(f"{basic.get('format', 'N/A')} ({file_info.get('mime_type', 'N/A')})", body_style)],
            [Paragraph("<b>Dimensions:</b>", cell_bold), Paragraph(f"{basic.get('width', 'N/A')} x {basic.get('height', 'N/A')} px", body_style),
             Paragraph("<b>File Size:</b>", cell_bold), Paragraph(str(file_info.get("file_size_formatted", "N/A")), body_style)],
            [Paragraph("<b>SHA-256 Hash:</b>", cell_bold), Paragraph(str(file_info.get("sha256", "N/A")), body_style),
             Paragraph("<b>Color Mode:</b>", cell_bold), Paragraph(str(basic.get("color_mode", "N/A")), body_style)]
        ]
        t_sum = Table(sum_data, colWidths=[90, 180, 90, 172])
        t_sum.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_sum)
        story.append(Spacer(1, 8))

        # --- Section 2: Privacy Risk Assessment ---
        story.append(Paragraph("2. PRIVACY RISK ASSESSMENT", section_style))
        score = risk.get("score", 0)
        level = risk.get("level", "LOW")
        
        level_colors = {
            "CRITICAL": colors.HexColor("#dc2626"),
            "HIGH": colors.HexColor("#ea580c"),
            "MEDIUM": colors.HexColor("#d97706"),
            "LOW": colors.HexColor("#16a34a")
        }
        badge_color = level_colors.get(level, colors.HexColor("#16a34a"))

        risk_data = [
            [
                Paragraph(f"<font size=24 color='{badge_color.hexval()}'><b>{score} / 100</b></font><br/><b>RISK SCORE</b>", ParagraphStyle('ScoreP', parent=body_style, alignment=1)),
                Paragraph(f"<font size=14 color='{badge_color.hexval()}'><b>LEVEL: {level}</b></font><br/><br/>{risk.get('summary_text', '')}", body_style)
            ]
        ]
        t_risk = Table(risk_data, colWidths=[140, 392])
        t_risk.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (-1,-1), 1, badge_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_risk)
        story.append(Spacer(1, 8))

        # --- Section 3: GPS / Location Intelligence ---
        story.append(Paragraph("3. GPS & LOCATION INTELLIGENCE", section_style))
        gps = metadata.get("gps", {})
        has_gps = gps.get("has_gps", False)

        if has_gps:
            # Prominent Alert
            alert_data = [[
                Paragraph("<b>⚠️ WARNING: GPS LOCATION EXPOSED</b><br/>"
                          "This image contains embedded geographic coordinates that pinpoint the capture location.", callout_text)
            ]]
            t_alert = Table(alert_data, colWidths=[532])
            t_alert.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fee2e2")),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#ef4444")),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t_alert)
            story.append(Spacer(1, 4))

            coords = gps.get("coordinates", {})
            lat = coords.get("latitude")
            lon = coords.get("longitude")
            nearest = gps.get("nearest_reference", {}) or {}
            loc_ref = nearest.get("readable_location", "Offline location reference unavailable")
            map_links = gps.get("map_links", {})

            gps_rows = [
                [Paragraph("<b>Coordinates (Dec):</b>", cell_bold), Paragraph(f"{lat:.6f}, {lon:.6f}", body_style),
                 Paragraph("<b>Precision:</b>", cell_bold), Paragraph(str(gps.get("precision", "N/A")), body_style)],
                [Paragraph("<b>Latitude (DMS):</b>", cell_bold), Paragraph(str(gps.get("latitude_dms", "N/A")), body_style),
                 Paragraph("<b>Longitude (DMS):</b>", cell_bold), Paragraph(str(gps.get("longitude_dms", "N/A")), body_style)],
                [Paragraph("<b>Altitude:</b>", cell_bold), Paragraph(str(gps.get("altitude", "Not found")), body_style),
                 Paragraph("<b>Offline Ref:</b>", cell_bold), Paragraph(str(loc_ref), body_style)],
                [Paragraph("<b>Map Links:</b>", cell_bold), Paragraph(f"Google Maps: {map_links.get('google_maps', 'N/A')}<br/>OSM: {map_links.get('openstreetmap', 'N/A')}", body_style),
                 Paragraph("<b>Address Note:</b>", cell_bold), Paragraph("Exact street address not determined without online geocoding.", body_style)]
            ]
        else:
            gps_rows = [
                [Paragraph("<b>Status:</b>", cell_bold), Paragraph("GPS coordinates not found", body_style)],
                [Paragraph("<b>Privacy Note:</b>", cell_bold), Paragraph("This image does not contain readable GPS metadata. This does not guarantee that the image is visually privacy-safe.", body_style)]
            ]

        t_gps = Table(gps_rows, colWidths=[110, 156, 90, 176] if has_gps else [110, 422])
        t_gps.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_gps)
        story.append(Spacer(1, 8))

        # --- Section 4: Camera & Device ---
        story.append(Paragraph("4. CAMERA & DEVICE INTELLIGENCE", section_style))
        norm_cam = metadata.get("normalized_exif", {}).get("camera", {})
        cam_rows = [
            [Paragraph("<b>Make:</b>", cell_bold), Paragraph(str(norm_cam.get("make", "Not found")), body_style),
             Paragraph("<b>Model:</b>", cell_bold), Paragraph(str(norm_cam.get("model", "Not found")), body_style)],
            [Paragraph("<b>Lens Make:</b>", cell_bold), Paragraph(str(norm_cam.get("lens_make", "Not found")), body_style),
             Paragraph("<b>Lens Model:</b>", cell_bold), Paragraph(str(norm_cam.get("lens_model", "Not found")), body_style)],
            [Paragraph("<b>Software:</b>", cell_bold), Paragraph(str(norm_cam.get("software", "Not found")), body_style),
             Paragraph("<b>Serial Number:</b>", cell_bold), Paragraph(str(norm_cam.get("body_serial_number", "Not found")), body_style)]
        ]
        t_cam = Table(cam_rows, colWidths=[90, 176, 90, 176])
        t_cam.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_cam)
        story.append(Spacer(1, 8))

        # --- Section 5: Date & Time ---
        story.append(Paragraph("5. DATE & TIME VECTORS", section_style))
        norm_time = metadata.get("normalized_exif", {}).get("timestamp", {})
        time_rows = [
            [Paragraph("<b>Captured (Original):</b>", cell_bold), Paragraph(str(norm_time.get("datetime_original", "Not found")), body_style),
             Paragraph("<b>Modified (File):</b>", cell_bold), Paragraph(str(norm_time.get("datetime", "Not found")), body_style)],
            [Paragraph("<b>Digitized Date:</b>", cell_bold), Paragraph(str(norm_time.get("datetime_digitized", "Not found")), body_style),
             Paragraph("<b>Timezone Offset:</b>", cell_bold), Paragraph(str(norm_time.get("timezone_offset", "Not found")), body_style)]
        ]
        t_time = Table(time_rows, colWidths=[120, 146, 110, 156])
        t_time.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_time)
        story.append(Spacer(1, 8))

        # --- Section 6 & 7: Identity, Copyright, IPTC & XMP ---
        story.append(Paragraph("6. IDENTITY, COPYRIGHT & IPTC/XMP VECTORS", section_style))
        norm_auth = metadata.get("normalized_exif", {}).get("author_copyright", {})
        iptc = metadata.get("iptc", {})
        xmp = metadata.get("xmp", {})

        id_rows = [
            [Paragraph("<b>Artist / Author:</b>", cell_bold), Paragraph(str(norm_auth.get("artist", "Not found")), body_style),
             Paragraph("<b>Copyright Notice:</b>", cell_bold), Paragraph(str(norm_auth.get("copyright", "Not found")), body_style)],
            [Paragraph("<b>IPTC Creator:</b>", cell_bold), Paragraph(str(iptc.get("author", "Not found")), body_style),
             Paragraph("<b>IPTC City / Country:</b>", cell_bold), Paragraph(f"{iptc.get('city', 'Not found')} / {iptc.get('country', 'Not found')}", body_style)],
            [Paragraph("<b>XMP Creator:</b>", cell_bold), Paragraph(str(xmp.get("creator", "Not found")), body_style),
             Paragraph("<b>XMP Document ID:</b>", cell_bold), Paragraph(str(xmp.get("document_id", "Not found")), body_style)]
        ]
        t_id = Table(id_rows, colWidths=[110, 156, 110, 156])
        t_id.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_id)
        story.append(Spacer(1, 8))

        # --- Section 8: Visual Privacy Analysis ---
        story.append(Paragraph("8. VISUAL PRIVACY ANALYSIS", section_style))
        vis = visual_results or {}
        vis_available = vis.get("available", False)
        
        if vis_available:
            faces_str = f"{vis.get('faces', {}).get('count', 0)} face(s) detected"
            text_str = vis.get('text', {}).get('details', 'None')
            qr_count = vis.get('qr_codes', {}).get('count', 0)
            bc_count = vis.get('barcodes', {}).get('count', 0)
            codes_str = f"{qr_count} QR code(s), {bc_count} barcode(s)"
            
            vis_rows = [
                [Paragraph("<b>Face Detection:</b>", cell_bold), Paragraph(faces_str, body_style),
                 Paragraph("<b>QR & Barcodes:</b>", cell_bold), Paragraph(codes_str, body_style)],
                [Paragraph("<b>Optical Text:</b>", cell_bold), Paragraph(text_str, body_style),
                 Paragraph("<b>Visual Level:</b>", cell_bold), Paragraph(f"<b>{vis.get('visual_risk_level', 'LOW')}</b> ({vis.get('visual_risk_score', 0)} pts)", body_style)]
            ]
        else:
            msg = vis.get("status_message") or "Visual analysis unavailable — optional local computer vision dependencies are not installed."
            vis_rows = [
                [Paragraph("<b>Status:</b>", cell_bold), Paragraph(msg, body_style)]
            ]

        t_vis = Table(vis_rows, colWidths=[110, 156, 110, 156] if vis_available else [110, 422])
        t_vis.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_vis)
        story.append(Spacer(1, 8))

        # --- Section 9: Findings & Exposures Table ---
        story.append(Paragraph("9. SENSITIVE METADATA & FORENSIC FINDINGS", section_style))
        findings = risk.get("findings", [])
        
        if findings:
            find_rows = [
                [Paragraph("<b>Category</b>", cell_bold), Paragraph("<b>Extracted Value</b>", cell_bold),
                 Paragraph("<b>Severity</b>", cell_bold), Paragraph("<b>Privacy Exposure & OSINT Impact</b>", cell_bold)]
            ]
            for f in findings:
                sev = f.get("severity", "LOW")
                sev_color = level_colors.get(sev, colors.HexColor("#64748b"))
                find_rows.append([
                    Paragraph(f.get("category", "General"), body_style),
                    Paragraph(f.get("value", "")[:50] + ("..." if len(f.get("value", "")) > 50 else ""), body_style),
                    Paragraph(f"<font color='{sev_color.hexval()}'><b>{sev} (+{f.get('contribution', 0)})</b></font>", body_style),
                    Paragraph(f.get("explanation", ""), body_style)
                ])
            t_find = Table(find_rows, colWidths=[100, 120, 80, 232])
            t_find.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(t_find)
        else:
            story.append(Paragraph("No sensitive metadata vectors or forensic identifiers were detected.", body_style))

        story.append(Spacer(1, 8))

        # --- Section 10: Actionable Recommendations ---
        recs = risk.get("recommendations", [])
        if recs:
            story.append(Paragraph("10. ACTIONABLE PRIVACY RECOMMENDATIONS", section_style))
            rec_rows = [[Paragraph(f"• {r}", body_style)] for r in recs]
            t_rec = Table(rec_rows, colWidths=[532])
            t_rec.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            story.append(t_rec)
            story.append(Spacer(1, 8))

        # --- Section 11 & 12: Sanitization / Before vs After ---
        if comp_results:
            story.append(Paragraph("11. SANITIZATION & COMPARISON ANALYSIS", section_style))
            orig_risk = comp_results.get("original", {}).get("risk", {})
            clean_risk = comp_results.get("cleaned", {}).get("risk", {})
            
            comp_table_data = [
                [Paragraph("<b>Metric</b>", cell_bold), Paragraph("<b>Original Image</b>", cell_bold), Paragraph("<b>Sanitized Image</b>", cell_bold)],
                [Paragraph("Risk Score", body_style), Paragraph(f"<b>{orig_risk.get('score', 'N/A')}</b> ({orig_risk.get('level', 'N/A')})", body_style), Paragraph(f"<b>{clean_risk.get('score', 'N/A')}</b> ({clean_risk.get('level', 'N/A')})", body_style)],
                [Paragraph("Findings Count", body_style), Paragraph(str(len(orig_risk.get("findings", []))), body_style), Paragraph(str(len(clean_risk.get("findings", []))), body_style)],
                [Paragraph("SHA-256 Hash", body_style), Paragraph(str(comp_results.get("original_sha256", "N/A"))[:32] + "...", body_style), Paragraph(str(comp_results.get("cleaned_sha256", "N/A"))[:32] + "...", body_style)],
                [Paragraph("Metadata Removed", body_style), Paragraph(", ".join(comp_results.get("removed_fields", ["None"])), body_style), Paragraph("Cleaned (Headers Stripped)", body_style)]
            ]
            t_comp = Table(comp_table_data, colWidths=[120, 206, 206])
            t_comp.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(t_comp)
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<i>{comp_results.get('notice', '')}</i>", ParagraphStyle('NoticeP', parent=body_style, fontName='Helvetica-Oblique', fontSize=7.5)))

        # Build document
        doc.build(story, canvasmaker=NumberedCanvas)
        return output_path
