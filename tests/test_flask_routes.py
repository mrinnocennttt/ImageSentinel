import unittest
import os
import json
import io
from app import app

class TestFlaskRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_01_index_page(self):
        """GET / returns HTML dashboard."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("ImageSentinel", html)
        self.assertIn("OSINT", html)
        self.assertIn("Visual Privacy", html)
        self.assertIn("GPS & Location Intelligence", html)

    def test_02_upload_valid_image(self):
        """POST /upload processes image, returns metadata, risk, visual, and report links."""
        with open("images/sample.jpg", "rb") as f:
            data = {
                'file': (io.BytesIO(f.read()), 'sample.jpg')
            }
        res = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data.get('success'))
        self.assertIn('metadata', json_data)
        self.assertIn('risk', json_data)
        self.assertIn('visual', json_data)
        self.assertIn('json_report', json_data)
        self.assertIn('pdf_report', json_data)

        # Check JSON report file accessibility
        report_url = json_data['json_report']
        rep_res = self.client.get(report_url)
        self.assertEqual(rep_res.status_code, 200)
        report_json = rep_res.get_json()
        self.assertIn('file', report_json)
        self.assertIn('risk_assessment', report_json)
        self.assertIn('metadata_extracted', report_json)
        self.assertIn('gps_analysis', report_json)
        self.assertIn('visual_analysis', report_json)
        self.assertIn('recommendations', report_json)

        # Check PDF report file accessibility
        pdf_url = json_data['pdf_report']
        pdf_res = self.client.get(pdf_url)
        self.assertEqual(pdf_res.status_code, 200)
        self.assertTrue(pdf_res.data.startswith(b'%PDF-'))

    def test_03_sanitize_route(self):
        """POST /sanitize strips metadata and returns before/after comparison."""
        res = self.client.post('/sanitize', json={'filename': 'sample.jpg'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('clean_filename', data)
        self.assertIn('comparison', data)
        self.assertIn('removed_fields', data['comparison'])

        clean_url = f"/cleaned/{data['clean_filename']}"
        clean_res = self.client.get(clean_url)
        self.assertEqual(clean_res.status_code, 200)

    def test_04_error_handling(self):
        """Verify error handling for invalid files and missing payloads."""
        # No file
        res = self.client.post('/upload', data={})
        self.assertEqual(res.status_code, 400)

        # Unsupported file
        data = {'file': (io.BytesIO(b"bad script"), 'malicious.exe')}
        res = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 400)
        self.assertIn('Unsupported file type', res.get_json()['error'])

        # Sanitize nonexistent file
        res = self.client.post('/sanitize', json={'filename': 'nonexistent_image_123.jpg'})
        self.assertEqual(res.status_code, 404)

if __name__ == '__main__':
    unittest.main()
