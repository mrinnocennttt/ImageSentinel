import unittest
import os
import shutil
from PIL import Image
import piexif
import cv2
from src.extractor import Extractor
from src.risk_engine import RiskEngine
from src.sanitizer import Sanitizer
from src.comparator import Comparator
from src.visual_analyzer import VisualPrivacyAnalyzer
from src.pdf_generator import PDFReportGenerator
from src.geo_intel import GeoIntel

class TestImageSentinel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs("tests/test_images", exist_ok=True)
        os.makedirs("tests/cleaned", exist_ok=True)
        os.makedirs("tests/reports", exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists("tests/test_images"):
            shutil.rmtree("tests/test_images", ignore_errors=True)
        if os.path.exists("tests/cleaned"):
            shutil.rmtree("tests/cleaned", ignore_errors=True)
        if os.path.exists("tests/reports"):
            shutil.rmtree("tests/reports", ignore_errors=True)

    def test_01_author_copyright_metadata(self):
        """TEST 1: Image containing EXIF author/copyright metadata -> Author/copyright findings."""
        img_path = "tests/test_images/test1_author.jpg"
        img = Image.new("RGB", (120, 120), color="blue")
        zeroth_ifd = {
            piexif.ImageIFD.Artist: b"Jane Doe Analyst",
            piexif.ImageIFD.Copyright: b"(C) 2026 Jane Doe"
        }
        exif_bytes = piexif.dump({"0th": zeroth_ifd})
        img.save(img_path, "jpeg", exif=exif_bytes)

        ext = Extractor(img_path)
        meta = ext.extract_all()
        risk = RiskEngine(meta).analyze()

        categories = [f["category"] for f in risk["findings"]]
        self.assertIn("Author / Creator", categories)
        self.assertIn("Copyright Notice", categories)

        author_finding = next(f for f in risk["findings"] if f["category"] == "Author / Creator")
        self.assertEqual(author_finding["value"], "Jane Doe Analyst")
        self.assertEqual(author_finding["severity"], "HIGH")

    def test_02_gps_metadata(self):
        """TEST 2: Image containing GPS metadata -> GPS coordinates + location warning + elevated risk."""
        img_path = "tests/test_images/test2_gps.jpg"
        img = Image.new("RGB", (120, 120), color="green")
        # Mumbai coordinates: 19° 4' 33.6" N, 72° 52' 39.7" E
        gps_ifd = {
            piexif.GPSIFD.GPSLatitudeRef: b'N',
            piexif.GPSIFD.GPSLatitude: ((19, 1), (4, 1), (3360, 100)),
            piexif.GPSIFD.GPSLongitudeRef: b'E',
            piexif.GPSIFD.GPSLongitude: ((72, 1), (52, 1), (3972, 100)),
            piexif.GPSIFD.GPSAltitude: (15, 1)
        }
        exif_bytes = piexif.dump({"GPS": gps_ifd})
        img.save(img_path, "jpeg", exif=exif_bytes)

        ext = Extractor(img_path)
        meta = ext.extract_all()
        self.assertTrue(meta["gps"]["has_gps"])
        self.assertAlmostEqual(meta["gps"]["coordinates"]["latitude"], 19.0760, places=2)
        self.assertAlmostEqual(meta["gps"]["coordinates"]["longitude"], 72.8777, places=2)

        risk = RiskEngine(meta).analyze()
        # Elevated score (at least 40 for GPS)
        self.assertGreaterEqual(risk["score"], 40)
        self.assertIn("CRITICAL EXPOSURE", risk["summary_text"])

        gps_findings = [f for f in risk["findings"] if "GPS" in f["category"]]
        self.assertTrue(len(gps_findings) > 0)
        self.assertEqual(gps_findings[0]["severity"], "CRITICAL")

    def test_03_no_metadata(self):
        """TEST 3: Image with no metadata -> 0 metadata findings, but NOT 'completely safe'."""
        img_path = "tests/test_images/test3_clean.png"
        img = Image.new("RGB", (80, 80), color="white")
        img.save(img_path, "PNG")

        ext = Extractor(img_path)
        meta = ext.extract_all()
        risk = RiskEngine(meta).analyze()

        self.assertEqual(len(risk["findings"]), 0)
        self.assertEqual(risk["score"], 0)
        self.assertEqual(risk["level"], "LOW")
        # Ensure it does NOT say "Safe to share"
        self.assertNotIn("safe to share", risk["summary_text"].lower())
        self.assertIn("visual content may still contain identifying information", risk["summary_text"].lower())

    def test_04_camera_information(self):
        """TEST 4: Image containing camera information -> Camera/device finding."""
        img_path = "tests/test_images/test4_camera.jpg"
        img = Image.new("RGB", (100, 100), color="purple")
        zeroth_ifd = {
            piexif.ImageIFD.Make: b"Sony",
            piexif.ImageIFD.Model: b"ILCE-7M4"
        }
        exif_bytes = piexif.dump({"0th": zeroth_ifd})
        img.save(img_path, "jpeg", exif=exif_bytes)

        ext = Extractor(img_path)
        meta = ext.extract_all()
        risk = RiskEngine(meta).analyze()

        cam_findings = [f for f in risk["findings"] if f["category"] == "Camera / Hardware"]
        self.assertEqual(len(cam_findings), 1)
        self.assertIn("Sony ILCE-7M4", cam_findings[0]["value"])
        self.assertEqual(cam_findings[0]["severity"], "MEDIUM")

    def test_05_visual_privacy_analysis(self):
        """TEST 5: Image with visible QR code -> Visual privacy finding."""
        img_path = "tests/test_images/test5_qr.png"
        # Generate synthetic QR code
        enc = cv2.QRCodeEncoder_create()
        qr_matrix = enc.encode("https://target.local/confidential_token")
        qr_big = cv2.resize(qr_matrix, (300, 300), interpolation=cv2.INTER_NEAREST)
        qr_padded = cv2.copyMakeBorder(qr_big, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=255)
        cv2.imwrite(img_path, qr_padded)

        vis = VisualPrivacyAnalyzer(img_path).analyze()
        self.assertTrue(vis["available"])
        self.assertTrue(vis["qr_codes"]["detected"])
        self.assertGreaterEqual(vis["qr_codes"]["count"], 1)

        meta = Extractor(img_path).extract_all()
        risk = RiskEngine(meta, vis).analyze()

        qr_findings = [f for f in risk["findings"] if "QR" in f["category"]]
        self.assertTrue(len(qr_findings) > 0)
        self.assertIn("Visual Privacy - QR Code", qr_findings[0]["category"])
        self.assertGreater(risk["visual_score"], 0)

    def test_06_sanitize_image(self):
        """TEST 6: Sanitize an image -> Metadata removal + before/after comparison."""
        img_path = "tests/test_images/test6_sample.jpg"
        img = Image.new("RGB", (100, 100), color="orange")
        zeroth_ifd = {
            piexif.ImageIFD.Make: b"Canon",
            piexif.ImageIFD.Model: b"EOS R5",
            piexif.ImageIFD.Artist: b"Investigator X"
        }
        exif_bytes = piexif.dump({"0th": zeroth_ifd})
        img.save(img_path, "jpeg", exif=exif_bytes)

        sanitizer = Sanitizer(img_path, "tests/cleaned")
        clean_path = sanitizer.sanitize()
        self.assertTrue(os.path.exists(clean_path))

        comp = Comparator(img_path, clean_path).compare()
        orig_score = comp["original"]["risk"]["score"]
        clean_score = comp["cleaned"]["risk"]["score"]

        self.assertGreater(orig_score, 0)
        self.assertEqual(clean_score, 0)
        self.assertIn("Camera / Hardware Profile", comp["removed_fields"])
        self.assertIn("Author / Creator Identity", comp["removed_fields"])
        self.assertNotEqual(comp["original_sha256"], comp["cleaned_sha256"])

    def test_07_pdf_generation(self):
        """TEST 7: Generate PDF -> Downloadable professional PDF report."""
        img_path = "tests/test_images/test7_pdf.jpg"
        img = Image.new("RGB", (100, 100), color="yellow")
        zeroth_ifd = {
            piexif.ImageIFD.Make: b"Nikon",
            piexif.ImageIFD.Model: b"Z9",
            piexif.ImageIFD.Artist: b"Photo Officer"
        }
        exif_bytes = piexif.dump({"0th": zeroth_ifd})
        img.save(img_path, "jpeg", exif=exif_bytes)

        ext = Extractor(img_path)
        meta = ext.extract_all()
        vis = VisualPrivacyAnalyzer(img_path).analyze()
        risk = RiskEngine(meta, vis).analyze()

        pdf_path = "tests/reports/test7_report.pdf"
        out = PDFReportGenerator.generate(meta, risk, vis, output_path=pdf_path)

        self.assertTrue(os.path.exists(out))
        file_size = os.path.getsize(out)
        self.assertGreater(file_size, 1000)
        with open(out, "rb") as f:
            header = f.read(5)
            self.assertEqual(header, b"%PDF-")


if __name__ == "__main__":
    unittest.main()
