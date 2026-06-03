# Humanoid Intelligence Report (PDF)

Manus-style layout: Jinja HTML + matplotlib charts + WeasyPrint PDF. Live data comes from `build_humanoid_intelligence_report_payload()`.

## Local reproduction

```bash
pip install jinja2 matplotlib weasyprint
PYTHONPATH=. python3 scripts/generate_humanoid_report_charts.py -d reports/charts
# Optional cover photo:
# cp your_photo.jpg app/report_assets/humanoid/robot_industrial.jpg
PYTHONPATH=. python3 scripts/generate_humanoid_report_pdf.py -o reports/humanoid_intelligence_report.pdf
```

HTML only (no WeasyPrint):

```bash
PYTHONPATH=. python3 scripts/generate_humanoid_report_pdf.py --html-only -o reports/report.html
```

## Production API

```bash
curl -o report.pdf "https://ready-2-robot.fly.dev/api/humanoid/intelligence-report/pdf?top_n=12"

Layout reference: `reports/Improving Report Layout, Content, Colors, and Graphics/` (HTML + charts + cover art). Production PDFs use WeasyPrint from `app/templates/humanoid_intelligence_report/report.html` with bundled `app/report_assets/humanoid/robot_industrial.jpg`.
```

If WeasyPrint or system libraries are missing on the host, the API falls back to ReportLab (no embedded charts).

## Files

| Path | Role |
|------|------|
| `app/templates/humanoid_intelligence_report/report.html` | Report layout (emerald `#10B981` theme) |
| `app/services/humanoid_report_charts.py` | Chart PNG generation |
| `app/services/humanoid_intelligence_report_render.py` | Context + WeasyPrint |
| `app/services/humanoid_intelligence_report_pdf.py` | PDF entry (WeasyPrint → ReportLab fallback) |
| `scripts/generate_humanoid_report_*.py` | Local CLI |
