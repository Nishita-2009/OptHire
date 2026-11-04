import json
import os

from agents.resume_matcher.parser import match_resume


def test_resume_matcher():

    with open(
        "outputs/parsed_resume.json",
        "r",
        encoding="utf-8"
    ) as file:

        resume = json.load(file)

    with open(
        "outputs/parsed_jd.json",
        "r",
        encoding="utf-8"
    ) as file:

        jd = json.load(file)

    result = match_resume(
        resume,
        jd
    )

    os.makedirs(
        "outputs",
        exist_ok=True
    )

    with open(
        "outputs/match_result.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n✅ Resume Matching Completed\n")

    print(json.dumps(
        result,
        indent=4
    ))


if __name__ == "__main__":

    test_resume_matcher()