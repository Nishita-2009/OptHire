import json
import os

from agents.jd_parser.parser import parse_job_description


def test_jd_parser():

    with open(
        "uploads/sample_jd.txt",
        "r",
        encoding="utf-8"
    ) as file:

        jd = file.read()

    parsed = parse_job_description(jd)

    os.makedirs("outputs", exist_ok=True)

    output = "outputs/parsed_jd.json"

    with open(output, "w", encoding="utf-8") as file:

        json.dump(
            parsed,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n✅ JD Parsed Successfully\n")

    print(json.dumps(parsed, indent=4))


if __name__ == "__main__":

    test_jd_parser()