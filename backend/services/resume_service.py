"""
AI Career Copilot - Resume Service

Service layer between the Flask API and ResumeAnalyzer.
The frontend never talks directly to ResumeAnalyzer; it calls the API,
and the API delegates resume analysis to this service.
"""

import os

from resume_analyzer import ResumeAnalyzer


class ResumeService:
    """Application service for resume analysis."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def __init__(self, analyzer=None):
        self.analyzer = analyzer or ResumeAnalyzer()

    def validate_file(self, file_path):
        """Validate that the uploaded file exists and is supported."""
        if not file_path:
            raise ValueError("No resume file path provided.")

        if not os.path.isfile(file_path):
            raise FileNotFoundError("Resume file not found.")

        extension = os.path.splitext(file_path)[1].lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                "Unsupported resume format. Use PDF, DOCX or TXT."
            )

        return True

    def analyze_resume(self, file_path):
        """Analyze a resume file through ResumeAnalyzer."""
        self.validate_file(file_path)

        result = self.analyzer.analyze_file(file_path)

        if not isinstance(result, dict):
            raise RuntimeError("Resume analyzer returned an invalid response.")

        if result.get("success") is False:
            raise ValueError(
                result.get("message") or
                "Resume analysis failed."
            )

        return result

    def get_supported_extensions(self):
        """Return supported resume extensions for API/UI use."""
        return sorted(self.SUPPORTED_EXTENSIONS)


# Shared service instance used by the Flask API.
resume_service = ResumeService()