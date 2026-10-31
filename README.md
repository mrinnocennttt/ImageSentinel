# ImageSentinel

**Image-Based OSINT Investigation and Privacy Risk Analysis System**

ImageSentinel is a powerful, locally-run Python CLI and Web Dashboard tool designed for OSINT investigators and cybersecurity professionals to analyze images for sensitive metadata, assess privacy risks, and sanitize files securely.

## Problem Statement
When images are shared online, they often contain hidden metadata (EXIF, XMP/IPTC) that can expose sensitive information such as exact GPS coordinates, camera models, unique device serial numbers, and creator identities. ImageSentinel automates the extraction, risk assessment, and removal of this data to protect privacy and aid in forensic investigations.

## Features
- **Comprehensive Extraction**: Extracts EXIF, XMP, IPTC, and basic image properties.
- **GPS Parsing**: Automatically converts raw GPS coordinates to decimal format.
- **Rule-Based Risk Scoring**: Transparent 0-100 privacy risk scoring based on the sensitivity of exposed data.
- **Metadata Sanitization**: Strips metadata to create a cleaned, safe-to-share copy without altering the original.
- **Comparison Engine**: Diff the original and sanitized image to prove effectiveness.
- **JSON Reporting**: Generate structured investigation reports for automation or record-keeping.
- **Web Dashboard**: Modern, dark-themed OSINT console for visual analysis.

## Architecture & Workflow
1. **Input**: A target image (JPG, PNG, WEBP, TIFF) is passed to the tool.
2. **Extraction Engine**: Uses `Pillow`, `exifread`, and `piexif` to read deeply embedded metadata.
3. **Risk Engine**: Scores the metadata against predefined privacy weights (e.g., GPS=+30).
4. **Sanitization**: Uses nuclear stripping (Pillow data re-creation) and `piexif` EXIF removal to sanitize the file.
5. **Reporting**: Displays results via a rich terminal UI or modern Web Dashboard.

## Installation on Kali Linux

1. Clone the repository or navigate to the project directory:
```bash
git clone https://github.com/yourusername/ImageSentinel.git
cd ImageSentinel
```

2. Create and activate a Python virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install requirements:
```bash
python3 -m pip install -r requirements.txt
```

## Usage Commands (CLI)

Get help:
```bash
python3 imagesentinel.py --help
```

Analyze an image:
```bash
python3 imagesentinel.py images/sample.jpg
```

Generate a JSON investigation report:
```bash
python3 imagesentinel.py images/sample.jpg --json
```

Analyze and sanitize (create a cleaned copy):
```bash
python3 imagesentinel.py images/sample.jpg --sanitize
```

Compare original vs cleaned images:
```bash
python3 imagesentinel.py --compare images/sample.jpg cleaned/sample_clean.jpg
```

## Usage (Web Dashboard)

Start the local web dashboard:
```bash
python3 app.py
```
Open your browser and navigate to `http://localhost:5000`.

## Project Structure
```text
ImageSentinel/
├── images/                  # Original target images
├── cleaned/                 # Sanitized image output
├── reports/                 # JSON investigation reports
├── src/                     # Core analysis engine
│   ├── extractor.py         # Metadata extraction logic
│   ├── risk_engine.py       # Rule-based privacy scoring
│   ├── sanitizer.py         # Safe metadata removal
│   ├── comparator.py        # Original vs Cleaned diff logic
│   └── reporter.py          # Terminal UI and JSON formatting
├── tests/                   # Automated test suite
├── templates/               # Web dashboard HTML templates
├── imagesentinel.py         # Main CLI entry point
├── app.py                   # Web dashboard backend (Flask)
├── requirements.txt         # Dependencies
├── README.md                # Project documentation
├── LICENSE                  # MIT License
└── SECURITY.md              # Security policies
```

## Technology Stack
- **Python 3** (Core Logic)
- **Pillow, exifread, piexif** (Metadata processing)
- **Rich** (Terminal UI)
- **Flask** (Web Dashboard Backend)
- **Tailwind CSS** (Web Dashboard Styling)

## Limitations
- Highly proprietary or corrupted RAW formats may not be fully supported.
- XMP data parsing is currently limited to raw string extraction without deep XML traversal.
- The sanitizer strips color profiles along with metadata to ensure privacy.

## Future Scope
- Integration with external threat intelligence feeds.
- Automated batch processing of directories.
- Support for video files (e.g., MP4 metadata).
- Deeper XMP/IPTC specific tag parsing.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements
Built using excellent open-source libraries including [Pillow](https://python-pillow.org/), [exifread](https://github.com/ianare/exif-py), [piexif](https://github.com/hMatoba/Piexif), and [Rich](https://github.com/Textualize/rich).
