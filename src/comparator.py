from src.extractor import Extractor
from src.risk_engine import RiskEngine
from src.visual_analyzer import VisualPrivacyAnalyzer

class Comparator:
    """Compares metadata and risk profiles between two images (original vs sanitized)."""
    
    def __init__(self, original_path, cleaned_path):
        self.original_path = original_path
        self.cleaned_path = cleaned_path
        
    def compare(self):
        # Extract and score original
        ext_orig = Extractor(self.original_path)
        meta_orig = ext_orig.extract_all()
        vis_orig = VisualPrivacyAnalyzer(self.original_path).analyze()
        risk_orig = RiskEngine(meta_orig, vis_orig).analyze()
        
        # Extract and score cleaned
        ext_clean = Extractor(self.cleaned_path)
        meta_clean = ext_clean.extract_all()
        vis_clean = VisualPrivacyAnalyzer(self.cleaned_path).analyze()
        risk_clean = RiskEngine(meta_clean, vis_clean).analyze()
        
        # Determine exactly which fields were removed
        removed_fields = []
        comparison_rows = []

        # 1. GPS
        orig_has_gps = meta_orig.get("gps", {}).get("has_gps", False)
        clean_has_gps = meta_clean.get("gps", {}).get("has_gps", False)
        if orig_has_gps:
            coords = meta_orig["gps"].get("coordinates", {})
            val = f"{coords.get('latitude', '')}, {coords.get('longitude', '')}"
            removed_fields.append("GPS Coordinates")
            comparison_rows.append({
                "field": "GPS Coordinates",
                "before": val,
                "after": "Removed" if not clean_has_gps else "Present",
                "status": "Removed" if not clean_has_gps else "Unchanged"
            })

        # 2. Camera / Device
        orig_cam = meta_orig.get("summary_fields", {}).get("camera", "Not found")
        clean_cam = meta_clean.get("summary_fields", {}).get("camera", "Not found")
        if orig_cam != "Not found":
            removed_fields.append("Camera / Hardware Profile")
            comparison_rows.append({
                "field": "Camera / Hardware",
                "before": orig_cam,
                "after": "Removed" if clean_cam == "Not found" else clean_cam,
                "status": "Removed" if clean_cam == "Not found" else "Unchanged"
            })

        # 3. Author / Creator
        orig_author = meta_orig.get("summary_fields", {}).get("author", "Not found")
        clean_author = meta_clean.get("summary_fields", {}).get("author", "Not found")
        if orig_author != "Not found":
            removed_fields.append("Author / Creator Identity")
            comparison_rows.append({
                "field": "Author / Creator",
                "before": orig_author,
                "after": "Removed" if clean_author == "Not found" else clean_author,
                "status": "Removed" if clean_author == "Not found" else "Unchanged"
            })

        # 4. Timestamp
        orig_dt = meta_orig.get("summary_fields", {}).get("datetime", "Not found")
        clean_dt = meta_clean.get("summary_fields", {}).get("datetime", "Not found")
        if orig_dt != "Not found":
            removed_fields.append("Capture Timestamp")
            comparison_rows.append({
                "field": "Timestamp",
                "before": orig_dt,
                "after": "Removed" if clean_dt == "Not found" else clean_dt,
                "status": "Removed" if clean_dt == "Not found" else "Unchanged"
            })

        # 5. Software
        orig_soft = meta_orig.get("summary_fields", {}).get("software", "Not found")
        clean_soft = meta_clean.get("summary_fields", {}).get("software", "Not found")
        if orig_soft != "Not found":
            removed_fields.append("Editing Software")
            comparison_rows.append({
                "field": "Software Tool",
                "before": orig_soft,
                "after": "Removed" if clean_soft == "Not found" else clean_soft,
                "status": "Removed" if clean_soft == "Not found" else "Unchanged"
            })

        # 6. Serial Number
        orig_sn = meta_orig.get("normalized_exif", {}).get("camera", {}).get("body_serial_number", "Not found")
        clean_sn = meta_clean.get("normalized_exif", {}).get("camera", {}).get("body_serial_number", "Not found")
        if orig_sn != "Not found":
            removed_fields.append("Device Serial Number")
            comparison_rows.append({
                "field": "Serial Number",
                "before": orig_sn,
                "after": "Removed" if clean_sn == "Not found" else clean_sn,
                "status": "Removed" if clean_sn == "Not found" else "Unchanged"
            })

        # 7. Copyright
        orig_copy = meta_orig.get("summary_fields", {}).get("copyright", "Not found")
        clean_copy = meta_clean.get("summary_fields", {}).get("copyright", "Not found")
        if orig_copy != "Not found":
            removed_fields.append("Copyright Tag")
            comparison_rows.append({
                "field": "Copyright Notice",
                "before": orig_copy,
                "after": "Removed" if clean_copy == "Not found" else clean_copy,
                "status": "Removed" if clean_copy == "Not found" else "Unchanged"
            })

        # 8. IPTC/XMP Location text
        orig_iptc_city = meta_orig.get("iptc", {}).get("city", "Not found")
        clean_iptc_city = meta_clean.get("iptc", {}).get("city", "Not found")
        if orig_iptc_city != "Not found":
            removed_fields.append("IPTC Location Text")
            comparison_rows.append({
                "field": "IPTC Location",
                "before": orig_iptc_city,
                "after": "Removed" if clean_iptc_city == "Not found" else clean_iptc_city,
                "status": "Removed" if clean_iptc_city == "Not found" else "Unchanged"
            })

        notice = (
            "Metadata headers and forensic tags have been removed. "
            "Please note: Sanitization does not alter visual pixels; visual features (faces, readable text, QR codes) remain present in the image."
        )

        return {
            "original": {
                "metadata": meta_orig,
                "risk": risk_orig,
                "visual": vis_orig
            },
            "cleaned": {
                "metadata": meta_clean,
                "risk": risk_clean,
                "visual": vis_clean
            },
            "removed_fields": removed_fields,
            "comparison_rows": comparison_rows,
            "original_sha256": meta_orig.get("file_info", {}).get("sha256", "Unknown"),
            "cleaned_sha256": meta_clean.get("file_info", {}).get("sha256", "Unknown"),
            "original_size": meta_orig.get("file_info", {}).get("file_size_formatted", "Unknown"),
            "cleaned_size": meta_clean.get("file_info", {}).get("file_size_formatted", "Unknown"),
            "notice": notice
        }
