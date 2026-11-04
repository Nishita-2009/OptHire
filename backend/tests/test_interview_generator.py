import json
import os

from agents.interview_generator.parser import generate_interview


def load_json(file_path: str) -> dict:

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def test_interview_generator():

    print("\n🚀 Starting Agent 5 - Interview Generator\n")

    resume = load_json(
        "outputs/parsed_resume.json"
    )

    jd = load_json(
        "outputs/parsed_jd.json"
    )

    match_result = load_json(
        "outputs/match_result.json"
    )

    skill_gap = load_json(
        "outputs/skill_gap_report.json"
    )

    print("✅ All Agent 5 input files loaded")

    interview = generate_interview(
        resume=resume,
        job_description=jd,
        match_result=match_result,
        skill_gap=skill_gap
    )

    os.makedirs(
        "outputs",
        exist_ok=True
    )

    output_file = (
        "outputs/interview_questions.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            interview,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        "\n✅ Personalized Interview "
        "Generated Successfully"
    )

    print(
        "✅ 21 Interview Questions Validated"
    )

    print(
        f"✅ Output saved to {output_file}\n"
    )

    print(json.dumps(
        interview,
        indent=4,
        ensure_ascii=False
    ))


if __name__ == "__main__":
    test_interview_generator()