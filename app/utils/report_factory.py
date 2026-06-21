"""
Report Factory (Factory Method Pattern)
=========================================
Dynamically delegates report generation to the appropriate strategy.
Demonstrates polymorphic object creation.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from fastapi.responses import StreamingResponse

from app.utils.csv_export import export_to_csv
from app.utils.pdf_export import generate_pdf_report

class ReportGenerator(ABC):
    """Abstract interface for all report generators."""
    @abstractmethod
    def generate(self, title: str, headers: List[str], data: List[Dict[str, Any]], filename: str) -> StreamingResponse:
        pass

class CSVReportGenerator(ReportGenerator):
    """Generates CSV reports."""
    def generate(self, title: str, headers: List[str], data: List[Dict[str, Any]], filename: str) -> StreamingResponse:
        # Title is ignored in standard CSV export but kept for interface compliance
        return export_to_csv(data, filename)

class PDFReportGenerator(ReportGenerator):
    """Generates PDF reports."""
    def generate(self, title: str, headers: List[str], data: List[Dict[str, Any]], filename: str) -> StreamingResponse:
        # Convert List[Dict] to List[List[str]] for PDF compatibility
        list_data = [[str(row.get(h, "")) for h in headers] for row in data]
        return generate_pdf_report(title, headers, list_data, filename)

class ReportFactory:
    """Factory to instantiate the correct report generator."""
    
    @staticmethod
    def get_generator(report_type: str) -> ReportGenerator:
        """Returns the appropriate ReportGenerator based on type string."""
        if report_type.lower() == 'csv':
            return CSVReportGenerator()
        elif report_type.lower() == 'pdf':
            return PDFReportGenerator()
        else:
            raise ValueError(f"Unsupported report format: {report_type}")
