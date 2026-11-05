"""
File Processing Service.
Handles safe temporary file handling, upload size validation,
and resume text extraction with guaranteed cleanup.
"""
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from fastapi import HTTPException, UploadFile, status

from config.settings import settings
from agents.resume_parser.pdf_reader import extract_resume_text


def validate_pdf_upload(file: UploadFile) -> None:
    """
    Validates that an uploaded file is a PDF and has a valid filename.
    Raises HTTPException with appropriate 4xx status codes.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty.",
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file extension '{file_ext}'. Only PDF files are accepted.",
        )


@contextmanager
def save_upload_to_temp_file(file: UploadFile) -> Generator[str, None, None]:
    """
    Context manager that streams an uploaded file to a temporary disk location,
    enforcing maximum size constraints, and guarantees cleanup on exit.
    """
    validate_pdf_upload(file)

    temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    total_bytes = 0

    try:
        with os.fdopen(temp_fd, "wb") as temp_file:
            # Stream in 64 KB chunks to protect memory
            chunk_size = 64 * 1024
            while True:
                chunk = file.file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Uploaded file exceeds maximum size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB.",
                    )
                temp_file.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        yield temp_path

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def extract_text_from_upload(file: UploadFile) -> str:
    """
    Safely saves the uploaded PDF to a temporary file, extracts text using pypdf,
    validates that text is non-empty, and cleans up the temporary file.
    """
    with save_upload_to_temp_file(file) as temp_path:
        try:
            extracted_text = extract_resume_text(temp_path)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unable to parse PDF content. Please ensure the file is a valid, readable PDF document.",
            ) from exc

    if not extracted_text or not extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded PDF contains no extractable text. Scanned or image-only PDFs are not supported without OCR.",
        )

    return extracted_text.strip()

