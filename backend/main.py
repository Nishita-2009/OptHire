import json
import os

from agents.resume_parser.pdf_reader import extract_resume_text
from agents.resume_parser.parser import parse_resume


def main():

    pdf_path = "uploads/Resume.pdf"

    resume_text = extract_resume_text(pdf_path)

    print("✅ Resume Loaded Successfully\n")

    parsed_resume = parse_resume(resume_text)

    print("✅ Resume Parsed Successfully\n")

    os.makedirs("outputs", exist_ok=True)

    output_file = "outputs/parsed_resume.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            parsed_resume,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"✅ JSON saved to {output_file}")


if __name__ == "__main__":
    main()