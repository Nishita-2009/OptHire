import json
import os

from agents.resume_parser.pdf_reader import extract_resume_text
from agents.resume_parser.parser import parse_resume


def test_resume_parser():
    candidate_paths = [
        "uploads/sample_resume_synthetic.pdf",
        "uploads/sample_resume.pdf",
        "uploads/Resume.pdf",
        "backend/uploads/sample_resume_synthetic.pdf",
        "backend/uploads/sample_resume.pdf",
    ]
    pdf_path = None
    for p in candidate_paths:
        if os.path.exists(p):
            pdf_path = p
            break

    if not pdf_path:
        raise FileNotFoundError("No resume PDF found in uploads directory.")

    print(f"\nLoading resume from: {pdf_path}")
    resume_text = extract_resume_text(pdf_path)

    print("\n✅ Resume Loaded Successfully\n")

    parsed_resume = parse_resume(resume_text)

    os.makedirs("outputs", exist_ok=True)

    output_file = "outputs/parsed_resume.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            parsed_resume,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("✅ Resume Parsed Successfully")
    print(f"\nOutput saved to:\n{output_file}")
    print("\nParsed Resume:\n")
    print(json.dumps(parsed_resume, indent=4))


if __name__ == "__main__":
    test_resume_parser()
