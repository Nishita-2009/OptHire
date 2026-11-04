import json
import os
from pathlib import Path

from agents.resume_parser.pdf_reader import extract_resume_text
from agents.resume_parser.parser import parse_resume


def main():
    potential_paths = [
        "uploads/sample_resume_synthetic.pdf",
        "uploads/sample_resume.pdf",
        "uploads/Resume.pdf",
        "backend/uploads/sample_resume_synthetic.pdf",
        "backend/uploads/sample_resume.pdf",
    ]
    pdf_path = None
    for p in potential_paths:
        if os.path.exists(p):
            pdf_path = p
            break

    if not pdf_path:
        raise FileNotFoundError(
            "No sample resume PDF found in uploads/. Please place a resume PDF in uploads/."
        )

    print(f"Loading resume from: {pdf_path}")
    resume_text = extract_resume_text(pdf_path)
    print("✅ Resume Loaded Successfully\n")

    parsed_resume = parse_resume(resume_text)
    print("✅ Resume Parsed Successfully\n")

    os.makedirs("outputs", exist_ok=True)
    output_file = "outputs/parsed_resume.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(parsed_resume, file, indent=4, ensure_ascii=False)

    print(f"✅ JSON saved to {output_file}")


if __name__ == "__main__":
    main()
