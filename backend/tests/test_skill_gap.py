import json
import os

from agents.skill_gap.parser import analyze_skill_gap


def test_skill_gap():

    with open("outputs/parsed_resume.json", "r", encoding="utf-8") as file:
        resume = json.load(file)

    with open("outputs/parsed_jd.json", "r", encoding="utf-8") as file:
        jd = json.load(file)

    with open("outputs/match_result.json", "r", encoding="utf-8") as file:
        match = json.load(file)

    result = analyze_skill_gap(
        resume,
        jd,
        match
    )

    os.makedirs("outputs", exist_ok=True)

    with open(
        "outputs/skill_gap_report.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n✅ Skill Gap Analysis Completed\n")
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    test_skill_gap()