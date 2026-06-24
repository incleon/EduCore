"""
PDF Export Utility using fpdf2
================================
"""

import io
from typing import List, Dict, Any
from fpdf import FPDF
from fastapi.responses import StreamingResponse


class CMSReport(FPDF):
    """
    Custom PDF report class — INHERITS from FPDF.

    OOP Concept: INHERITANCE + METHOD OVERRIDING
    """

    def header(self):
        """Override: Custom header for every page."""
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Enterprise College Management System", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, "Confidential Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        """Override: Custom footer with page number."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def generate_pdf_report(
    title: str,
    headers: List[str],
    data: List[List[str]],
    filename: str = "report.pdf",
) -> StreamingResponse:
    """Generate a PDF table report."""
    pdf = CMSReport()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Table header
    pdf.set_font("Helvetica", "B", 9)
    col_width = (pdf.w - 20) / len(headers)
    for header in headers:
        pdf.cell(col_width, 8, header, border=1, align="C")
    pdf.ln()

    # Table data
    pdf.set_font("Helvetica", "", 8)
    for row in data:
        for cell in row:
            pdf.cell(col_width, 7, str(cell)[:30], border=1)
        pdf.ln()

    # Output
    output = io.BytesIO()
    pdf_content = pdf.output()
    output.write(pdf_content)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
