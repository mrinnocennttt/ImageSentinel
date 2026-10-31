class RiskEngine:
    """
    Transparent, rule-based privacy risk engine for OSINT metadata & visual analysis.
    Evaluates exposure impact rather than merely counting metadata tags.
    """

    # Transparent scoring model weights
    SCORE_WEIGHTS = {
        "gps_coordinates": 40,      # CRITICAL: exact physical coordinates
        "location_text": 15,        # HIGH: textual city/country/sublocation
        "gps_altitude_error": 5,    # HIGH: 3D altitude or positioning precision
        "author_identity": 15,      # HIGH: author, creator, artist
        "camera_device": 10,        # MEDIUM: camera make, model, lens
        "timestamp": 10,            # MEDIUM: capture/original timestamp
        "software": 5,              # MEDIUM: editing software / creator tool
        "unique_identifiers": 10,   # HIGH: camera/lens serial numbers, document IDs
        "copyright": 5,             # LOW: copyright string
        "other_metadata": 5,        # LOW: IPTC/XMP present without identity
        "visual_faces": 15,         # HIGH: human faces visually detected
        "visual_qr": 10,            # MEDIUM: QR code payload visually detected
        "visual_barcode": 10,       # MEDIUM: Barcode payload visually detected
        "visual_text": 10           # MEDIUM: High-confidence OCR text detected
    }

    def __init__(self, metadata, visual_results=None):
        self.metadata = metadata or {}
        self.visual_results = visual_results or {}
        self.score = 0
        self.metadata_score = 0
        self.visual_score = 0
        self.findings = []
        self.exposures = []
        self.score_breakdown = []
        self.recommendations = []

    def analyze(self):
        self.findings = []
        self.exposures = []
        self.score_breakdown = []
        self.recommendations = []
        self.metadata_score = 0
        self.visual_score = 0

        # 1. Metadata Exposure Checks
        self._check_gps()
        self._check_location_text()
        self._check_author_identity()
        self._check_camera_device()
        self._check_timestamp()
        self._check_software()
        self._check_unique_identifiers()
        self._check_copyright()
        self._check_other_metadata()

        # 2. Visual Privacy Checks (if visual_results supplied)
        self._check_visual_exposures()

        # Deduplicate recommendations while preserving order
        unique_recs = []
        for r in self.recommendations:
            if r and r not in unique_recs:
                unique_recs.append(r)
        self.recommendations = unique_recs

        # Total capped score
        self.score = min(self.metadata_score + self.visual_score, 100)
        overall_level = self._get_level_for_score(self.score)
        meta_level = self._get_level_for_score(min(self.metadata_score, 100))
        vis_level = self._get_level_for_score(min(self.visual_score, 100))

        # Overall summary explanation
        summary_text = self._build_summary_text()

        return {
            "score": self.score,
            "level": overall_level,
            "metadata_score": min(self.metadata_score, 100),
            "metadata_level": meta_level,
            "visual_score": min(self.visual_score, 100),
            "visual_level": vis_level,
            "findings": self.findings,
            "exposures": self.exposures,
            "score_breakdown": self.score_breakdown,
            "why_this_score": self.score_breakdown,
            "recommendations": self.recommendations,
            "summary_text": summary_text
        }

    @staticmethod
    def _get_level_for_score(score):
        if score <= 20:
            return "LOW"
        elif score <= 50:
            return "MEDIUM"
        elif score <= 75:
            return "HIGH"
        else:
            return "CRITICAL"

    def _add_finding(self, category, value, severity, weight_key, explanation, recommendation, is_visual=False):
        pts = self.SCORE_WEIGHTS.get(weight_key, 0)
        finding_item = {
            "category": category,
            "value": str(value),
            "severity": severity,
            "contribution": pts,
            "points": pts,
            "explanation": explanation,
            "recommendation": recommendation,
            "is_visual": is_visual
        }
        self.findings.append(finding_item)
        self.exposures.append(explanation)
        self.score_breakdown.append({
            "factor": category,
            "value": str(value),
            "contribution": f"+{pts}",
            "points": pts,
            "severity": severity,
            "explanation": explanation
        })
        if recommendation:
            self.recommendations.append(recommendation)

        if is_visual:
            self.visual_score += pts
        else:
            self.metadata_score += pts

    def _check_gps(self):
        coords = self.metadata.get("gps", {}).get("coordinates")
        if coords and coords.get("latitude") is not None and coords.get("longitude") is not None:
            lat = coords["latitude"]
            lon = coords["longitude"]
            val = f"{lat:.6f}, {lon:.6f}"
            precision = self.metadata.get("gps", {}).get("precision", "Sub-meter")
            self._add_finding(
                category="GPS Location",
                value=val,
                severity="CRITICAL",
                weight_key="gps_coordinates",
                explanation=f"Exact physical location is exposed ({val}) with precision estimate: {precision}. Reveals capture location, daily routine, or residence.",
                recommendation="Remove GPS metadata before sharing or publishing."
            )

            # Altitude / vertical positioning
            alt = self.metadata.get("gps", {}).get("altitude")
            if alt and alt != "Not found":
                self._add_finding(
                    category="GPS Altitude",
                    value=str(alt),
                    severity="HIGH",
                    weight_key="gps_altitude_error",
                    explanation=f"Vertical elevation ({alt}) is exposed, enabling 3D elevation positioning and floor/altitude profiling.",
                    recommendation="Sanitize GPS altitude and 3D positioning metadata."
                )

    def _check_location_text(self):
        iptc = self.metadata.get("iptc", {})
        xmp = self.metadata.get("xmp", {})

        loc_parts = []
        for f in [iptc.get("city"), iptc.get("province_state"), iptc.get("country"), xmp.get("location")]:
            if f and f != "Not found" and f not in loc_parts:
                loc_parts.append(f)

        if loc_parts:
            val = ", ".join(loc_parts)
            self._add_finding(
                category="Location Text Fields",
                value=val,
                severity="HIGH",
                weight_key="location_text",
                explanation=f"Embedded location description ({val}) identifies the municipality, state, or country of origin.",
                recommendation="Strip IPTC and XMP geographic text tags."
            )

    def _check_author_identity(self):
        norm = self.metadata.get("normalized_exif", {}).get("author_copyright", {})
        iptc = self.metadata.get("iptc", {})
        xmp = self.metadata.get("xmp", {})

        author_cands = [norm.get("artist"), iptc.get("author"), iptc.get("creator"), xmp.get("creator")]
        author_valid = [a for a in author_cands if a and a != "Not found"]

        if author_valid:
            author_val = author_valid[0]
            self._add_finding(
                category="Author / Creator",
                value=author_val,
                severity="HIGH",
                weight_key="author_identity",
                explanation=f"Directly identifies the author or creator ({author_val}), facilitating social profiling and correlation across online accounts.",
                recommendation="Strip creator identity tags prior to distribution."
            )

    def _check_camera_device(self):
        norm = self.metadata.get("normalized_exif", {}).get("camera", {})
        make = norm.get("make")
        model = norm.get("model")
        lens = norm.get("lens_model")

        parts = [p for p in [make, model] if p and p != "Not found"]
        if not parts:
            # Fallback check raw exif
            exif = self.metadata.get("exif", {})
            raw_exif = self.metadata.get("raw_exif", {})
            m = exif.get("Make") or raw_exif.get("Image Make")
            mod = exif.get("Model") or raw_exif.get("Image Model")
            parts = [str(p) for p in [m, mod] if p and str(p).lower() != "none"]

        if parts:
            cam_str = " ".join(parts)
            if lens and lens != "Not found":
                cam_str += f" | Lens: {lens}"
            self._add_finding(
                category="Camera / Hardware",
                value=cam_str,
                severity="MEDIUM",
                weight_key="camera_device",
                explanation=f"Reveals physical capture hardware ({cam_str}). Enables device fingerprinting, financial profiling, or equipment tracking.",
                recommendation="Remove EXIF device tags to obscure hardware details."
            )

    def _check_timestamp(self):
        norm = self.metadata.get("normalized_exif", {}).get("timestamp", {})
        dt = norm.get("datetime_original") or norm.get("datetime")
        if not dt or dt == "Not found":
            exif = self.metadata.get("exif", {})
            raw_exif = self.metadata.get("raw_exif", {})
            dt = exif.get("DateTimeOriginal") or exif.get("DateTime") or raw_exif.get("EXIF DateTimeOriginal")

        if dt and str(dt).strip() and str(dt).lower() != "none" and str(dt) != "Not found":
            self._add_finding(
                category="Capture Timestamp",
                value=str(dt),
                severity="MEDIUM",
                weight_key="timestamp",
                explanation=f"Indicates exact activity timestamp ({dt}), allowing adversaries to establish personal movement timelines, schedules, and routines.",
                recommendation="Scrub capture timestamps from EXIF and XMP."
            )

    def _check_software(self):
        norm = self.metadata.get("normalized_exif", {}).get("camera", {})
        xmp = self.metadata.get("xmp", {})
        software = norm.get("software") or xmp.get("software")
        if not software or software == "Not found":
            exif = self.metadata.get("exif", {})
            raw_exif = self.metadata.get("raw_exif", {})
            software = exif.get("Software") or raw_exif.get("Image Software")

        if software and str(software).strip() and str(software).lower() != "none" and str(software) != "Not found":
            self._add_finding(
                category="Editing Software",
                value=str(software),
                severity="LOW",
                weight_key="software",
                explanation=f"Discloses software and post-processing tools ({software}), hinting at operating system or editing toolchains.",
                recommendation="Sanitize software processing tags."
            )

    def _check_unique_identifiers(self):
        raw_exif = self.metadata.get("raw_exif", {})
        norm = self.metadata.get("normalized_exif", {}).get("camera", {})
        xmp = self.metadata.get("xmp", {})

        serials = []
        body_sn = norm.get("body_serial_number") or raw_exif.get("EXIF BodySerialNumber")
        lens_sn = norm.get("lens_serial_number") or raw_exif.get("EXIF LensSerialNumber")
        doc_id = xmp.get("document_id")

        if body_sn and body_sn != "Not found":
            serials.append(f"Body S/N: {body_sn}")
        if lens_sn and lens_sn != "Not found":
            serials.append(f"Lens S/N: {lens_sn}")
        if doc_id and doc_id != "Not found":
            serials.append(f"DocID: {doc_id}")

        if serials:
            val = "; ".join(serials)
            self._add_finding(
                category="Hardware / Asset Serial Number",
                value=val,
                severity="HIGH",
                weight_key="unique_identifiers",
                explanation=f"Unique hardware or asset identifier exposed ({val}). Enables high-confidence forensic linking across unrelated images.",
                recommendation="Strip proprietary maker notes and unique serial identifiers."
            )

    def _check_copyright(self):
        norm = self.metadata.get("normalized_exif", {}).get("author_copyright", {})
        iptc = self.metadata.get("iptc", {})
        xmp = self.metadata.get("xmp", {})

        copy_cands = [norm.get("copyright"), iptc.get("copyright"), xmp.get("copyright")]
        copy_valid = [c for c in copy_cands if c and c != "Not found"]

        if copy_valid:
            val = copy_valid[0]
            self._add_finding(
                category="Copyright Notice",
                value=val,
                severity="LOW",
                weight_key="copyright",
                explanation=f"Copyright string ({val}) may disclose organizational affiliation, legal entity, or identity.",
                recommendation="Review copyright tags before distribution."
            )

    def _check_other_metadata(self):
        # Check if XMP or IPTC data is present when no specific serial was flagged
        xmp = self.metadata.get("xmp", {})
        has_xmp = bool(xmp.get("raw_xmp")) or bool(self.metadata.get("xmp_iptc", {}).get("raw_xmp"))
        # Only add if not already heavily penalized
        if has_xmp and self.metadata_score < 70 and not any(f["category"] == "Hardware / Asset Serial Number" for f in self.findings):
            self._add_finding(
                category="XMP / Adobe Metadata Packet",
                value="XMP Packet Present",
                severity="LOW",
                weight_key="other_metadata",
                explanation="Image contains an XMP data packet which may house editing history, original file paths, or private metadata.",
                recommendation="Strip full XMP data blocks during sanitization."
            )

    def _check_visual_exposures(self):
        if not self.visual_results:
            return

        # Faces
        faces = self.visual_results.get("faces", {})
        if faces.get("detected") and faces.get("count", 0) > 0:
            count = faces["count"]
            self._add_finding(
                category="Visual Privacy - Human Faces",
                value=f"{count} face(s) visually detected",
                severity="HIGH",
                weight_key="visual_faces",
                explanation=f"{count} human face(s) detected in the visual frame. Visual exposure creates biometric and person-identification risk regardless of metadata.",
                recommendation="Blur, mask, or crop facial regions if personal privacy is required.",
                is_visual=True
            )

        # QR Codes
        qr = self.visual_results.get("qr_codes", {})
        if qr.get("detected") and qr.get("count", 0) > 0:
            payloads = qr.get("payloads", [])
            val = f"{qr['count']} code(s)" + (f": {payloads[0]}" if payloads else "")
            self._add_finding(
                category="Visual Privacy - QR Code",
                value=val,
                severity="MEDIUM",
                weight_key="visual_qr",
                explanation="Scannable QR code detected in the image containing embedded URLs or machine-readable identifiers.",
                recommendation="Obscure or verify QR code payloads prior to sharing.",
                is_visual=True
            )

        # Barcodes
        bc = self.visual_results.get("barcodes", {})
        if bc.get("detected") and bc.get("count", 0) > 0:
            payloads = bc.get("payloads", [])
            val = f"{bc['count']} barcode(s)"
            self._add_finding(
                category="Visual Privacy - Barcode",
                value=val,
                severity="MEDIUM",
                weight_key="visual_barcode",
                explanation="Barcode detected in the image containing product or tracking serial numbers.",
                recommendation="Obscure barcode patterns before sharing.",
                is_visual=True
            )

        # Text
        text = self.visual_results.get("text", {})
        if text.get("detected"):
            samples = text.get("samples", [])
            if samples:
                val = f"Text detected: {' '.join(samples[:5])}"
                self._add_finding(
                    category="Visual Privacy - Optical Text",
                    value=val,
                    severity="MEDIUM",
                    weight_key="visual_text",
                    explanation="Readable optical text was identified in the image, potentially exposing names, locations, license plates, or contact details.",
                    recommendation="Redact sensitive optical text before public release.",
                    is_visual=True
                )

    def _build_summary_text(self):
        has_gps = self.metadata.get("gps", {}).get("has_gps", False)
        has_meta_findings = len([f for f in self.findings if not f.get("is_visual")]) > 0
        has_vis_findings = len([f for f in self.findings if f.get("is_visual")]) > 0

        if has_gps:
            return "CRITICAL EXPOSURE: Geographic coordinates are embedded in this image, exposing exact physical capture location."
        elif self.score >= 51:
            return "Significant privacy vectors identified across metadata and/or visual analysis. Sanitization highly recommended."
        elif self.score >= 21:
            return "Moderate privacy metadata or visual indicators detected. Consider reviewing identified vectors before sharing."
        else:
            if not has_meta_findings and not has_vis_findings:
                return "No sensitive metadata was detected. Visual content may still contain identifying information."
            elif not has_meta_findings and has_vis_findings:
                return "Metadata is clean, but visual content may still reveal information."
            else:
                return "No sensitive metadata was detected. Visual content may still contain identifying information."
