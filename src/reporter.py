import json
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from src.pdf_generator import PDFReportGenerator

console = Console()

class Reporter:
    """Handles formatted output to the terminal, structured JSON reporting, and PDF generation."""
    
    @staticmethod
    def print_header():
        header = Text("ImageSentinel: OSINT Image Privacy & Metadata Analysis System", style="bold cyan", justify="center")
        console.print(Panel(header, box=box.DOUBLE, expand=False))
        console.print()

    @staticmethod
    def print_analysis(metadata, risk, filepath, visual_results=None):
        console.print(f"[bold yellow]Analyzing:[/] {filepath}")
        console.print(f"[bold yellow]SHA-256:[/] {metadata.get('file_info', {}).get('sha256', 'N/A')}")
        
        # Risk Score Panel
        score = risk.get('score', 0)
        level = risk.get('level', 'LOW')
        
        if level == "LOW":
            color = "green"
        elif level == "MEDIUM":
            color = "yellow"
        elif level == "HIGH":
            color = "orange3"
        else:
            color = "bold white on red"
            
        risk_text = Text(f"Privacy Risk Score: {score}/100 | Level: {level}\n{risk.get('summary_text', '')}", style=color)
        console.print(Panel(risk_text, title="Privacy Risk Assessment", expand=False))

        # GPS Warning if present
        gps = metadata.get("gps", {})
        if gps.get("has_gps"):
            coords = gps.get("coordinates", {})
            gps_warning = Text(
                f"[!] GPS LOCATION EXPOSED: {coords.get('latitude', '')}, {coords.get('longitude', '')}\n"
                f"Precision: {gps.get('precision', 'N/A')} | {gps.get('nearest_reference', {}).get('readable_location', '')}",
                style="bold red"
            )
            console.print(Panel(gps_warning, box=box.ROUNDED, expand=False))
        
        # Findings Table
        findings = risk.get('findings', [])
        if findings:
            table = Table(title="Identified Sensitive Metadata & Forensic Vectors", box=box.ROUNDED, style="cyan")
            table.add_column("Category", style="magenta")
            table.add_column("Extracted Value", style="green")
            table.add_column("Severity", style="bold red")
            table.add_column("OSINT Exposure Impact", style="white")
            
            for item in findings:
                val = str(item.get('value', ''))
                val_disp = val[:50] + ("..." if len(val) > 50 else "")
                sev = item.get('severity', 'LOW')
                table.add_row(item.get('category', ''), val_disp, sev, item.get('explanation', ''))
                
            console.print(table)
        else:
            console.print("[bold green]No sensitive metadata vectors found![/]")

        # Visual Privacy Summary
        if visual_results and visual_results.get("available"):
            console.print(f"[bold cyan]Visual Privacy:[/] Faces: {visual_results.get('faces', {}).get('count', 0)} | "
                          f"QR Codes: {visual_results.get('qr_codes', {}).get('count', 0)} | "
                          f"Barcodes: {visual_results.get('barcodes', {}).get('count', 0)}")
            
        console.print()

    @staticmethod
    def print_comparison(comp_results):
        console.print("[bold cyan]=== Original vs Cleaned Comparison ===[/]")
        
        orig_risk = comp_results['original']['risk']
        clean_risk = comp_results['cleaned']['risk']
        
        table = Table(box=box.ROUNDED)
        table.add_column("Metric", style="magenta")
        table.add_column("Original", style="red")
        table.add_column("Cleaned", style="green")
        
        table.add_row(
            "Risk Score", 
            f"{orig_risk['score']} ({orig_risk['level']})", 
            f"{clean_risk['score']} ({clean_risk['level']})"
        )
        table.add_row(
            "Findings Count", 
            str(len(orig_risk['findings'])), 
            str(len(clean_risk['findings']))
        )
        table.add_row(
            "SHA-256", 
            str(comp_results.get('original_sha256', 'N/A'))[:20] + "...", 
            str(comp_results.get('cleaned_sha256', 'N/A'))[:20] + "..."
        )
        table.add_row(
            "Removed Fields",
            ", ".join(comp_results.get('removed_fields', ["None"])),
            "Stripped"
        )
        
        console.print(table)
        console.print(f"[italic yellow]{comp_results.get('notice', '')}[/]")

    @staticmethod
    def generate_json_report(metadata, risk, filepath, visual_results=None, comp_results=None, output_dir="reports"):
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.basename(filepath)
        name, _ = os.path.splitext(filename)
        report_path = os.path.join(output_dir, f"{name}_report.json")
        
        report_data = {
            "file": {
                "filepath": filepath,
                "filename": filename,
                "file_info": metadata.get("file_info", {}),
                "basic_info": metadata.get("basic_info", {})
            },
            "risk_assessment": {
                "score": risk.get("score", 0),
                "level": risk.get("level", "LOW"),
                "metadata_score": risk.get("metadata_score", 0),
                "metadata_level": risk.get("metadata_level", "LOW"),
                "visual_score": risk.get("visual_score", 0),
                "visual_level": risk.get("visual_level", "LOW"),
                "summary_text": risk.get("summary_text", ""),
                "why_this_score": risk.get("why_this_score", []),
                "findings": risk.get("findings", [])
            },
            "metadata_extracted": {
                "normalized_exif": metadata.get("normalized_exif", {}),
                "summary_fields": metadata.get("summary_fields", {}),
                "exif_tags": metadata.get("exif", {}),
                "iptc": metadata.get("iptc", {}),
                "xmp": metadata.get("xmp", {}),
                "raw_exif": metadata.get("raw_exif", {})
            },
            "gps_analysis": metadata.get("gps", {}),
            "visual_analysis": visual_results or {},
            "recommendations": risk.get("recommendations", []),
            "sanitization": comp_results or {}
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4)
            
        console.print(f"[bold green]JSON report saved to:[/] {report_path}")
        return report_path

    @staticmethod
    def generate_pdf_report(metadata, risk, filepath, visual_results=None, comp_results=None, output_dir="reports"):
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.basename(filepath)
        name, _ = os.path.splitext(filename)
        report_path = os.path.join(output_dir, f"{name}_report.pdf")
        
        PDFReportGenerator.generate(
            metadata=metadata,
            risk=risk,
            visual_results=visual_results,
            comp_results=comp_results,
            output_path=report_path
        )
        console.print(f"[bold green]PDF report saved to:[/] {report_path}")
        return report_path
