import os
import re
import html

# Try importing computer vision dependencies
CV2_AVAILABLE = False
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    pass

PYTESSERACT_AVAILABLE = False
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pass


class VisualPrivacyAnalyzer:
    """
    Performs privacy-oriented local visual analysis on images:
    - Face detection count (NO identity recognition, NO identifying individuals)
    - QR code detection & safe payload extraction (NO auto-opening URLs)
    - Barcode detection & safe payload extraction
    - High-confidence text / OCR region detection
    Gracefully falls back if dependencies are not installed or models are unavailable.
    """

    def __init__(self, image_path, model_path="models/yunet.onnx"):
        self.image_path = image_path
        self.model_path = model_path
        self.results = {
            "available": False,
            "status_message": "",
            "faces": {
                "detected": False,
                "count": 0,
                "details": "No faces detected."
            },
            "qr_codes": {
                "detected": False,
                "count": 0,
                "payloads": []
            },
            "barcodes": {
                "detected": False,
                "count": 0,
                "payloads": []
            },
            "text": {
                "detected": False,
                "regions_count": 0,
                "samples": [],
                "details": "No readable text detected."
            },
            "visual_risk_level": "LOW",
            "visual_risk_score": 0,
            "exposures": []
        }

    def analyze(self):
        if not CV2_AVAILABLE:
            self.results["available"] = False
            self.results["status_message"] = (
                "Visual analysis unavailable — optional local computer vision dependencies are not installed."
            )
            return self.results

        if not os.path.exists(self.image_path):
            self.results["status_message"] = "Image file not found for visual analysis."
            return self.results

        try:
            # Load image using OpenCV
            # Handle unicode paths safely on Windows
            img_bytes = np.fromfile(self.image_path, dtype=np.uint8)
            img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

            if img is None:
                self.results["status_message"] = "Could not decode image for visual analysis."
                return self.results

            self.results["available"] = True
            self.results["status_message"] = "Visual analysis completed using local computer vision engine."

            # 1. Detect QR Codes
            self._detect_qr(img)

            # 2. Detect Barcodes
            self._detect_barcodes(img)

            # 3. Detect Faces (Strictly count only, no identity recognition)
            self._detect_faces(img)

            # 4. Detect Text / OCR Regions
            self._detect_text(img)

            # 5. Compute Visual Privacy Risk & Exposures
            self._evaluate_visual_risk()

        except Exception as e:
            self.results["available"] = False
            self.results["status_message"] = f"Visual analysis encountered an error: {str(e)}"

        return self.results

    def _detect_qr(self, img):
        try:
            qr_detector = cv2.QRCodeDetector()
            # Try multi-detection first, fallback to single
            decoded_text = ""
            if hasattr(qr_detector, "detectAndDecodeMulti"):
                ok, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(img)
                if ok and decoded_info:
                    for text in decoded_info:
                        if text:
                            clean_text = self._sanitize_payload(text)
                            self.results["qr_codes"]["payloads"].append(clean_text)
            
            if not self.results["qr_codes"]["payloads"]:
                decoded_text, points, _ = qr_detector.detectAndDecode(img)
                if decoded_text:
                    clean_text = self._sanitize_payload(decoded_text)
                    self.results["qr_codes"]["payloads"].append(clean_text)

            payloads = self.results["qr_codes"]["payloads"]
            if payloads:
                self.results["qr_codes"]["detected"] = True
                self.results["qr_codes"]["count"] = len(payloads)
        except Exception:
            pass

    def _detect_barcodes(self, img):
        try:
            if hasattr(cv2, "barcode_BarcodeDetector"):
                bc_detector = cv2.barcode_BarcodeDetector()
                res = bc_detector.detectAndDecode(img)
                if res and len(res) >= 2:
                    decoded_info = res[0]
                    decoded_type = res[1]
                    if isinstance(decoded_info, (list, tuple)):
                        for i, val in enumerate(decoded_info):
                            if val:
                                b_type = str(decoded_type[i]) if (isinstance(decoded_type, (list, tuple)) and i < len(decoded_type)) else "Barcode"
                                self.results["barcodes"]["payloads"].append({
                                    "type": b_type,
                                    "data": self._sanitize_payload(str(val))
                                })
                    elif isinstance(decoded_info, str) and decoded_info.strip():
                        b_type = str(decoded_type) if decoded_type else "Barcode"
                        self.results["barcodes"]["payloads"].append({
                            "type": b_type,
                            "data": self._sanitize_payload(decoded_info)
                        })

                if self.results["barcodes"]["payloads"]:
                    self.results["barcodes"]["detected"] = True
                    self.results["barcodes"]["count"] = len(self.results["barcodes"]["payloads"])
        except Exception:
            pass

    def _detect_faces(self, img):
        try:
            h, w = img.shape[:2]
            if os.path.exists(self.model_path) and hasattr(cv2, "FaceDetectorYN"):
                # Scale down for faster detection if image is huge
                max_dim = 1280
                scale = 1.0
                if max(h, w) > max_dim:
                    scale = max_dim / float(max(h, w))
                    resized = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                else:
                    resized = img

                rh, rw = resized.shape[:2]
                detector = cv2.FaceDetectorYN.create(
                    self.model_path,
                    "",
                    (rw, rh),
                    score_threshold=0.75,
                    nms_threshold=0.3,
                    top_k=50
                )
                detector.setInputSize((rw, rh))
                _, faces = detector.detect(resized)

                if faces is not None and len(faces) > 0:
                    count = int(len(faces))
                    self.results["faces"]["detected"] = True
                    self.results["faces"]["count"] = count
                    self.results["faces"]["details"] = (
                        f"{count} human face(s) visually detected. Note: Facial recognition is not performed."
                    )
                else:
                    self.results["faces"]["detected"] = False
                    self.results["faces"]["count"] = 0
                    self.results["faces"]["details"] = "No human faces detected in image."
            else:
                self.results["faces"]["details"] = (
                    "Face detection model not found locally; face scan skipped."
                )
        except Exception as e:
            self.results["faces"]["details"] = f"Face detection error: {str(e)}"

    def _detect_text(self, img):
        """
        Detect candidate text regions using morphological gradient analysis.
        If pytesseract and tesseract binary are available, perform OCR with strict confidence check.
        Never fabricate or claim text if confidence is poor.
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # Morphological gradient to detect candidate text blocks
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
            grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
            _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            # Connect text components horizontally
            close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (19, 5))
            connected = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel)
            
            contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            candidate_regions = 0
            for c in contours:
                x, y, cw, ch = cv2.boundingRect(c)
                aspect = cw / float(ch) if ch > 0 else 0
                area = cw * ch
                # Filter for typical text line aspect ratios and sizes
                if aspect > 1.5 and cw > 25 and ch > 8 and (area / (w * h) < 0.35):
                    candidate_regions += 1

            self.results["text"]["regions_count"] = min(candidate_regions, 50)

            # Try Tesseract OCR if available
            ocr_text_found = False
            if PYTESSERACT_AVAILABLE:
                try:
                    # Request TSV/data with confidence
                    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
                    n_boxes = len(data['text'])
                    reliable_words = []

                    for i in range(n_boxes):
                        word = data['text'][i].strip()
                        conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
                        # Filter: confidence > 70%, length > 2, alphanumeric characters
                        if conf >= 70 and len(word) >= 3 and re.search(r'[a-zA-Z0-9]', word):
                            reliable_words.append(word)

                    if reliable_words:
                        ocr_text_found = True
                        sample = " ".join(reliable_words[:20])
                        self.results["text"]["detected"] = True
                        self.results["text"]["samples"] = reliable_words[:15]
                        self.results["text"]["details"] = (
                            f"Readable text detected with high confidence: \"{self._sanitize_payload(sample)}\""
                        )
                except Exception:
                    # Tesseract binary not installed or failed
                    pass

            if not ocr_text_found:
                if candidate_regions >= 2:
                    self.results["text"]["detected"] = True
                    self.results["text"]["details"] = (
                        f"{candidate_regions} potential text/symbol region(s) detected via morphological contrast analysis. (Local OCR engine not configured)."
                    )
                else:
                    self.results["text"]["detected"] = False
                    self.results["text"]["details"] = "No readable text or prominent text blocks detected."

        except Exception as e:
            self.results["text"]["details"] = f"Text analysis error: {str(e)}"

    def _evaluate_visual_risk(self):
        score = 0
        exposures = []

        if self.results["faces"]["detected"] and self.results["faces"]["count"] > 0:
            score += 15
            count = self.results["faces"]["count"]
            exposures.append({
                "category": "Visual - Human Faces",
                "value": f"{count} face(s) detected",
                "severity": "HIGH",
                "contribution": 15,
                "explanation": "Image visually exposes human faces, increasing biometric or interpersonal identification risk.",
                "recommendation": "Blur or crop faces before public disclosure if identity privacy is required."
            })

        if self.results["qr_codes"]["detected"] and self.results["qr_codes"]["count"] > 0:
            score += 10
            payload_str = ", ".join(self.results["qr_codes"]["payloads"][:3])
            exposures.append({
                "category": "Visual - QR Code",
                "value": f"{self.results['qr_codes']['count']} code(s): {payload_str}",
                "severity": "MEDIUM",
                "contribution": 10,
                "explanation": "Embedded QR code contains encoded machine-readable data, URLs, or potential tracking identifiers.",
                "recommendation": "Inspect and sanitize or obscure QR code payloads before sharing."
            })

        if self.results["barcodes"]["detected"] and self.results["barcodes"]["count"] > 0:
            score += 10
            bc_str = ", ".join([b.get("data", "") for b in self.results["barcodes"]["payloads"][:3]])
            exposures.append({
                "category": "Visual - Barcode",
                "value": f"{self.results['barcodes']['count']} barcode(s): {bc_str}",
                "severity": "MEDIUM",
                "contribution": 10,
                "explanation": "Barcode detected which may expose serial numbers, tracking IDs, or product information.",
                "recommendation": "Obscure or crop barcode markers before public distribution."
            })

        if self.results["text"]["detected"]:
            if self.results["text"]["samples"]:
                score += 10
                samples_str = " ".join(self.results["text"]["samples"][:6])
                exposures.append({
                    "category": "Visual - Embedded Text",
                    "value": f"Text detected: \"{samples_str}\"",
                    "severity": "MEDIUM",
                    "contribution": 10,
                    "explanation": "Image contains readable optical text that may expose names, locations, license plates, or contact data.",
                    "recommendation": "Review and redact sensitive optical text elements."
                })
            elif self.results["text"]["regions_count"] >= 3:
                score += 5
                exposures.append({
                    "category": "Visual - Text Regions",
                    "value": f"{self.results['text']['regions_count']} dense contrast regions",
                    "severity": "LOW",
                    "contribution": 5,
                    "explanation": "Image exhibits high-density contrast regions consistent with printed or digital text.",
                    "recommendation": "Visually inspect image for visible private text or signage."
                })

        self.results["visual_risk_score"] = min(score, 40)
        if score == 0:
            self.results["visual_risk_level"] = "LOW"
        elif score <= 10:
            self.results["visual_risk_level"] = "LOW"
        elif score <= 20:
            self.results["visual_risk_level"] = "MEDIUM"
        else:
            self.results["visual_risk_level"] = "HIGH"

        self.results["exposures"] = exposures

    def _sanitize_payload(self, text):
        """Sanitize decoded strings to prevent HTML injection and excessive length."""
        if not text:
            return ""
        text = str(text).strip()
        text = html.escape(text)
        if len(text) > 100:
            return text[:97] + "..."
        return text
