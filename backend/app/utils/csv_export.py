"""
CSV Export Utility
====================

Strategy Pattern: Different export formats (CSV, PDF)
share the same interface but produce different outputs.
"""

import csv
import io
from typing import List, Dict, Any
from fastapi.responses import StreamingResponse


def export_to_csv(data: List[Dict[str, Any]], filename: str = "export.csv") -> StreamingResponse:
    """Generate a CSV file from a list of dictionaries."""
    if not data:
        output = io.StringIO()
        output.write("No data available")
        output.seek(0)
    else:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
