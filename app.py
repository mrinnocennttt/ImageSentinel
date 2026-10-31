import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
from src.extractor import Extractor
from src.risk_engine import RiskEngine
from src.sanitizer import Sanitizer
from src.comparator import Comparator
from src.visual_analyzer import VisualPrivacyAnalyzer
from src.reporter import Reporter

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'images'
app.config['CLEANED_FOLDER'] = 'cleaned'
app.config['REPORTS_FOLDER'] = 'reports'
app.config['MAX_CONTENT_LENGTH'] = 24 * 1024 * 1024  # 24 MB max
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'tiff', 'tif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CLEANED_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_safe_filepath(folder, filename):
    """Prevent directory traversal attacks."""
    clean_name = os.path.basename(filename)
    safe_dir = os.path.abspath(folder)
    target_path = os.path.abspath(os.path.join(safe_dir, clean_name))
    if not target_path.startswith(safe_dir):
        return None
    return target_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in upload request.'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No image file was selected.'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({
            'error': f'Unsupported file type. Please upload a valid JPG, PNG, WEBP, or TIFF image.'
        }), 400

    try:
        raw_name = secure_filename(file.filename)
        if not raw_name:
            raw_name = f"image_{uuid.uuid4().hex[:8]}.jpg"

        # Prevent duplicate file collision by checking existence
        name_stem, ext = os.path.splitext(raw_name)
        target_name = raw_name
        counter = 1
        while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], target_name)):
            target_name = f"{name_stem}_{counter}{ext}"
            counter += 1

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], target_name)
        file.save(filepath)

        # 1. Metadata Extraction
        extractor = Extractor(filepath)
        metadata = extractor.extract_all()

        # 2. Local Visual Privacy Analysis
        visual_analyzer = VisualPrivacyAnalyzer(filepath)
        visual_results = visual_analyzer.analyze()

        # 3. Privacy Risk Engine
        risk_engine = RiskEngine(metadata, visual_results)
        risk = risk_engine.analyze()

        # 4. Generate Initial JSON & PDF Reports
        base_name, _ = os.path.splitext(target_name)
        json_report_path = Reporter.generate_json_report(
            metadata=metadata,
            risk=risk,
            filepath=filepath,
            visual_results=visual_results,
            output_dir=app.config['REPORTS_FOLDER']
        )
        pdf_report_path = Reporter.generate_pdf_report(
            metadata=metadata,
            risk=risk,
            filepath=filepath,
            visual_results=visual_results,
            output_dir=app.config['REPORTS_FOLDER']
        )

        return jsonify({
            'success': True,
            'filename': target_name,
            'metadata': metadata,
            'risk': risk,
            'visual': visual_results,
            'json_report': f"/reports/{os.path.basename(json_report_path)}",
            'pdf_report': f"/reports/{os.path.basename(pdf_report_path)}"
        })

    except Exception as e:
        return jsonify({'error': f'Image analysis failed: {str(e)}'}), 500

@app.route('/sanitize', methods=['POST'])
def sanitize_file():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid request payload.'}), 400
        
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Filename is required for sanitization.'}), 400
        
    filepath = get_safe_filepath(app.config['UPLOAD_FOLDER'], filename)
    if not filepath or not os.path.exists(filepath):
        return jsonify({'error': 'Target image file not found on server.'}), 404
        
    try:
        # Sanitize metadata while preserving visual quality
        sanitizer = Sanitizer(filepath, app.config['CLEANED_FOLDER'])
        clean_path = sanitizer.sanitize()
        clean_filename = os.path.basename(clean_path)

        # Compare original vs sanitized
        comparator = Comparator(filepath, clean_path)
        comp_results = comparator.compare()

        # Update JSON and PDF reports to include sanitization audit
        base_name, _ = os.path.splitext(filename)
        json_report_path = Reporter.generate_json_report(
            metadata=comp_results['original']['metadata'],
            risk=comp_results['original']['risk'],
            filepath=filepath,
            visual_results=comp_results['original']['visual'],
            comp_results=comp_results,
            output_dir=app.config['REPORTS_FOLDER']
        )
        pdf_report_path = Reporter.generate_pdf_report(
            metadata=comp_results['original']['metadata'],
            risk=comp_results['original']['risk'],
            filepath=filepath,
            visual_results=comp_results['original']['visual'],
            comp_results=comp_results,
            output_dir=app.config['REPORTS_FOLDER']
        )

        return jsonify({
            'success': True,
            'clean_filename': clean_filename,
            'comparison': comp_results,
            'json_report': f"/reports/{os.path.basename(json_report_path)}",
            'pdf_report': f"/reports/{os.path.basename(pdf_report_path)}"
        })
    except Exception as e:
        return jsonify({'error': f'Sanitization failed: {str(e)}'}), 500

@app.route('/images/<filename>')
def uploaded_file(filename):
    safe_path = get_safe_filepath(app.config['UPLOAD_FOLDER'], filename)
    if not safe_path or not os.path.exists(safe_path):
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(filename))

@app.route('/cleaned/<filename>')
def cleaned_file(filename):
    safe_path = get_safe_filepath(app.config['CLEANED_FOLDER'], filename)
    if not safe_path or not os.path.exists(safe_path):
        abort(404)
    return send_from_directory(app.config['CLEANED_FOLDER'], os.path.basename(filename), as_attachment=True)

@app.route('/reports/<filename>')
def report_file(filename):
    safe_path = get_safe_filepath(app.config['REPORTS_FOLDER'], filename)
    if not safe_path or not os.path.exists(safe_path):
        abort(404)
    return send_from_directory(app.config['REPORTS_FOLDER'], os.path.basename(filename))

@app.route('/report/pdf/<filename>')
def download_pdf(filename):
    base, _ = os.path.splitext(filename)
    pdf_filename = f"{base}_report.pdf"
    safe_path = get_safe_filepath(app.config['REPORTS_FOLDER'], pdf_filename)
    if not safe_path or not os.path.exists(safe_path):
        abort(404)
    return send_from_directory(app.config['REPORTS_FOLDER'], pdf_filename, as_attachment=True)

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'Image file is too large (maximum allowed size is 24 MB).'}), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'The requested resource was not found.'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
