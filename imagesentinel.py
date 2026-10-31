#!/usr/bin/env python3
import argparse
import sys
import os
from src.extractor import Extractor
from src.risk_engine import RiskEngine
from src.sanitizer import Sanitizer
from src.comparator import Comparator
from src.visual_analyzer import VisualPrivacyAnalyzer
from src.reporter import Reporter, console

def main():
    parser = argparse.ArgumentParser(
        description="ImageSentinel: Image-Based OSINT Investigation and Privacy Risk Analysis System"
    )
    
    # Handle arguments
    parser.add_argument("image", nargs="?", help="Path to the image file to analyze")
    parser.add_argument("--json", action="store_true", help="Generate a JSON investigation report")
    parser.add_argument("--pdf", action="store_true", help="Generate a professional PDF investigation report")
    parser.add_argument("--sanitize", action="store_true", help="Sanitize metadata and save a cleaned copy")
    parser.add_argument("--compare", nargs=2, metavar=('ORIGINAL', 'CLEANED'), help="Compare original vs cleaned image metadata")

    args = parser.parse_args()

    Reporter.print_header()

    if args.compare:
        orig_path, clean_path = args.compare
        try:
            comp = Comparator(orig_path, clean_path)
            results = comp.compare()
            Reporter.print_comparison(results)
        except Exception as e:
            console.print(f"[bold red]Error during comparison:[/] {str(e)}")
            sys.exit(1)
        return

    if not args.image:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.image):
        console.print(f"[bold red]Error:[/] File not found: {args.image}")
        sys.exit(1)

    try:
        # 1. Extract metadata
        extractor = Extractor(args.image)
        metadata = extractor.extract_all()

        # 2. Visual Privacy Analysis
        visual_analyzer = VisualPrivacyAnalyzer(args.image)
        visual_results = visual_analyzer.analyze()

        # 3. Privacy Risk Engine
        risk_engine = RiskEngine(metadata, visual_results)
        risk = risk_engine.analyze()

        # 4. Print results to terminal
        Reporter.print_analysis(metadata, risk, args.image, visual_results)

        comp_results = None

        # 5. Sanitize image if requested
        if args.sanitize:
            console.print("[bold cyan]Sanitizing image...[/]")
            sanitizer = Sanitizer(args.image, "cleaned")
            clean_path = sanitizer.sanitize()
            console.print(f"[bold green]Sanitized image saved to:[/] {clean_path}")
            
            # Show comparison
            comp = Comparator(args.image, clean_path)
            comp_results = comp.compare()
            Reporter.print_comparison(comp_results)

        # 6. Generate JSON report
        if args.json:
            Reporter.generate_json_report(metadata, risk, args.image, visual_results, comp_results)

        # 7. Generate PDF report
        if args.pdf:
            Reporter.generate_pdf_report(metadata, risk, args.image, visual_results, comp_results)

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
