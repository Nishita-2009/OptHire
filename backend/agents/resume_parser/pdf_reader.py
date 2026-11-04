from pypdf import PdfReader


def extract_resume_text(pdf_path: str) -> str:
    """
    Reads a PDF resume and returns the extracted text.
    """

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text