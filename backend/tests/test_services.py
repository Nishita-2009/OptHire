"""
Unit tests for Core Services:
- json_service (markdown fence cleaning, safe parsing)
- file_service (file validation, upload size limit, temp file cleanup)
- gemini_service (factory, invocation wrapper, error handling)
"""
import io
import pytest
from fastapi import HTTPException, UploadFile

from services.json_service import clean_json_markdown, parse_json_safely
from services.file_service import validate_pdf_upload, save_upload_to_temp_file
from services.gemini_service import GeminiService
from tests.conftest import MockAIMessage, MockLLM


def test_clean_json_markdown():
    # Test standard json fence
    raw1 = "```json\n{\"key\": \"val\"}\n```"
    assert clean_json_markdown(raw1) == '{"key": "val"}'

    # Test plain fence
    raw2 = "```\n{\"key\": \"val\"}\n```"
    assert clean_json_markdown(raw2) == '{"key": "val"}'

    # Test already clean json
    raw3 = '{"key": "val"}'
    assert clean_json_markdown(raw3) == '{"key": "val"}'


def test_parse_json_safely_success():
    raw = "```json\n{\"name\": \"OptHire\", \"count\": 7}\n```"
    data = parse_json_safely(raw, context="Test")
    assert data["name"] == "OptHire"
    assert data["count"] == 7


def test_parse_json_safely_failure():
    with pytest.raises(ValueError, match="Invalid JSON in Test"):
        parse_json_safely("NOT JSON CONTENT", context="Test")


def test_validate_pdf_upload_valid():
    file = UploadFile(filename="resume.pdf", file=io.BytesIO(b"dummy pdf bytes"))
    validate_pdf_upload(file)  # Should not raise


def test_validate_pdf_upload_invalid_extension():
    file = UploadFile(filename="resume.docx", file=io.BytesIO(b"dummy docx bytes"))
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_upload(file)
    assert exc_info.value.status_code == 415


def test_validate_pdf_upload_empty_filename():
    file = UploadFile(filename="", file=io.BytesIO(b"dummy bytes"))
    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_upload(file)
    assert exc_info.value.status_code == 400


def test_save_upload_to_temp_file_empty_content():
    file = UploadFile(filename="empty.pdf", file=io.BytesIO(b""))
    with pytest.raises(HTTPException) as exc_info:
        with save_upload_to_temp_file(file):
            pass
    assert exc_info.value.status_code == 400


def test_save_upload_to_temp_file_oversized(monkeypatch):
    from config import settings
    # Monkeypatch max upload size to 100 bytes for fast test
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 100)

    big_content = b"A" * 200
    file = UploadFile(filename="big.pdf", file=io.BytesIO(big_content))
    with pytest.raises(HTTPException) as exc_info:
        with save_upload_to_temp_file(file):
            pass
    assert exc_info.value.status_code == 413


def test_gemini_service_invoke_and_parse_json():
    service = GeminiService(api_key="test_key")
    mock_llm = MockLLM('```json\n{"status": "ok"}\n```')

    data = service.invoke_and_parse_json("Prompt", llm=mock_llm)
    assert data["status"] == "ok"


def test_gemini_service_missing_key(monkeypatch):
    service = GeminiService(api_key="")
    monkeypatch.setattr(service, "api_key", "")
    with pytest.raises(ValueError, match="Gemini API key is not configured"):
        service.create_llm()
