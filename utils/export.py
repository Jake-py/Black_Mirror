"""
Export utilities for Black Mirror reports.
TXT, HTML, PDF formats.
"""

from core.models import ScanSession
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import os

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    import jinja2
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


class Exporter:
    """Export manager for scan sessions."""

    @staticmethod
    def to_dict(session: ScanSession) -> Dict[str, Any]:
        """Convert session to exportable dict."""
        return {
            "timestamp": session.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": f"{session.duration:.2f}s" if session.duration else "N/A",
            "status": session.status.value,
            "counts": session.get_counts(),
            "results": [r.to_dict() for r in session.results],
            "results_by_type": {
                pt.value: [r.to_dict() for r in session.get_by_type(pt)] 
                for pt in ProtectionType
            }
        }

    @staticmethod
    def export_txt(session: ScanSession, path: str = None) -> str:
        """Export as plain TXT."""
        data = Exporter.to_dict(session)
        timestamp = data["timestamp"].replace(":", "-").replace(" ", "_")
        path = path or f"black_mirror_{timestamp}.txt"
        
        content = f"""Black Mirror Security Report
Generated: {data['timestamp']}
Duration: {data['duration']}
Overall Status: {data['status'].upper()}
Summary: OK={data['counts']['ok']}, WARN={data['counts']['warn']}, RISK={data['counts']['risk']}

"""
        
        for result in data["results"]:
            status_emoji = {"OK": "✓", "WARN": "⚠", "RISK": "✗"}.get(result["status"], "?")
            content += f"{status_emoji} {result['name']} ({result['type']})\n"
            content += f"  Status: {result['status']}\n"
            content += f"  {result['description']}\n"
            if result["recommendation"]:
                content += f"  Fix: {result['recommendation']}\n"
            if result.get("fix_command"):
                content += f"  Command: {result['fix_command']}\n"
            content += "\n"
        
        Path(path).write_text(content)
        return path

    @staticmethod
    def export_html(session: ScanSession, path: str = None) -> str:
        """Export as HTML."""
        if not HAS_JINJA2:
            return "Jinja2 not installed"
        
        data = Exporter.to_dict(session)
        timestamp = data["timestamp"].replace(":", "-").replace(" ", "_")
        path = path or f"black_mirror_{timestamp}.html"
        
        # Inline styles for standalone HTML
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Black Mirror Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #0d0d0d; color: #fff; margin: 0; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .status-{{status.lower()}} {{ color: {{status_colors[status]}}; font-weight: bold; font-size: 24px; }}
        .result {{ background: #1a1a1a; margin: 10px 0; padding: 20px; border-radius: 8px; border-left: 5px solid {{status_colors[status]}}; }}
        .fix {{ background: #333; padding: 10px; border-radius: 4px; font-family: monospace; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ background: #252525; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Black Mirror Security Report</h1>
        <p>Generated: {{timestamp}} | Duration: {{duration}} | Status: <span class="status-{{status.lower()}}">{{status}}</span></p>
        <p>OK: {{counts.ok}} | ⚠ WARN: {{counts.warn}} | ✗ RISK: {{counts.risk}}</p>
    </div>
    
    {% for result in results %}
    <div class="result">
        <h3><span class="status-{{result.status.lower()}}">{{result.status}}</span> {{result.name}} ({{result.type}})</h3>
        <p>{{result.description}}</p>
        {% if result.recommendation %}
        <div class="fix">💡 {{result.recommendation}}</div>
        {% endif %}
        {% if result.fix_command %}
        <div class="fix">⚡ <code>{{result.fix_command}}</code></div>
        {% endif %}
        {% if result.details %}
        <details><summary>Детали</summary><pre>{{result.details}}</pre></details>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
        """
        
        env = jinja2.Environment()
        template = env.from_string(html_template)
        html_content = template.render(
            **data,
            status_colors={"OK": "#4caf50", "WARN": "#ff9800", "RISK": "#f44336", "UNKNOWN": "#9e9e9e"}
        )
        
        Path(path).write_text(html_content)
        return path

    @staticmethod
    def export_pdf(session: ScanSession, path: str = None) -> str:
        """Export as PDF."""
        if not HAS_REPORTLAB:
            return "reportlab not installed"
        
        data = Exporter.to_dict(session)
        timestamp = data["timestamp"].replace(":", "-").replace(" ", "_")
        path = path or f"black_mirror_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"<b>🛡️ Black Mirror Security Report</b><br/>"
                         f"Generated: {data['timestamp']} | "
                         f"Duration: {data['duration']} | "
                         f"Status: <font color='#4caf50'>{data['status']}</font>", 
                         styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Summary table
        summary_data = [
            ["Status", "OK", "WARN", "RISK", "Unknown"],
            [data['status'], str(data['counts']['ok']), str(data['counts']['warn']),
             str(data['counts']['risk']), str(data['counts']['unknown'])]
        ]
        table = Table(summary_data)
        table.setStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 14),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ])
        story.append(table)
        story.append(Spacer(1, 24))
        
        # Results
        for result in data["results"]:
            status_color = {"OK": "#4caf50", "WARN": "#ff9800", "RISK": "#f44336"}.get(result["status"], "#9e9e9e")
            p = Paragraph(f"<b><font color='{status_color}'>{result['status']}</font> {result['name']}</b><br/>"
                         f"{result['description']}<br/>"
                         f"<i>{result.get('recommendation', '')}</i>", styles['Normal'])
            story.append(p)
            if result.get("fix_command"):
                fix_p = Paragraph(f"<font color='#00ffff'>Fix: <code>{result['fix_command']}</code></font>", 
                                styles['Code'])
                story.append(fix_p)
            story.append(Spacer(1, 12))
        
        doc.build(story)
        return path


if __name__ == "__main__":
    print("Export utils ready.")
