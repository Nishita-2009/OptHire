import json
import os

from agents.hiring_report.generator import (
    generate_hiring_report
)


def load_json(
    file_path: str
) -> dict:
    """
    Loads a required JSON file.
    """

    if not os.path.exists(
        file_path
    ):

        raise FileNotFoundError(
            f"Required file not found: "
            f"{file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )


def save_json(
    file_path: str,
    data: dict
):
    """
    Saves the final report as formatted JSON.
    """

    os.makedirs(
        "outputs",
        exist_ok=True
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def test_hiring_report():

    print(
        "\n" + "=" * 60
    )

    print(
        "📊 OPTHIRE FINAL HIRING REPORT"
    )

    print(
        "=" * 60
    )

    # -----------------------------------
    # Load outputs from previous agents
    # -----------------------------------

    print(
        "\n📂 Loading previous agent outputs..."
    )

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

    interview_summary = load_json(
        "outputs/interview_summary.json"
    )

    print(
        "✅ Resume data loaded"
    )

    print(
        "✅ Job description loaded"
    )

    print(
        "✅ ATS match result loaded"
    )

    print(
        "✅ Skill gap report loaded"
    )

    print(
        "✅ Interview summary loaded"
    )

    # -----------------------------------
    # Generate final report
    # -----------------------------------

    print(
        "\n🤖 Agent 7 is analyzing "
        "the complete candidate journey..."
    )

    report = generate_hiring_report(
        resume=resume,
        job_description=jd,
        match_result=match_result,
        skill_gap=skill_gap,
        interview_summary=interview_summary
    )

    # -----------------------------------
    # Save final report
    # -----------------------------------

    output_file = (
        "outputs/final_hiring_report.json"
    )

    save_json(
        output_file,
        report
    )

    # -----------------------------------
    # Extract important values
    # -----------------------------------

    candidate = report.get(
        "candidate",
        {}
    )

    scores = report.get(
        "scores",
        {}
    )

    final_decision = report.get(
        "final_decision",
        {}
    )

    candidate_name = candidate.get(
        "name",
        "Unknown Candidate"
    )

    target_role = candidate.get(
        "target_role",
        "Unknown Role"
    )

    resume_score = scores.get(
        "resume_match_score",
        0
    )

    interview_score = scores.get(
        "interview_score",
        0
    )

    final_score = scores.get(
        "final_hiring_score",
        0
    )

    confidence = scores.get(
        "decision_confidence",
        0
    )

    recommendation = final_decision.get(
        "recommendation",
        "Not Available"
    )

    risk_level = final_decision.get(
        "risk_level",
        "Not Available"
    )

    next_action = final_decision.get(
        "next_action",
        "Not Available"
    )

    # -----------------------------------
    # Display final result
    # -----------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "✅ FINAL HIRING REPORT GENERATED"
    )

    print(
        "=" * 60
    )

    print(
        f"\nCandidate: {candidate_name}"
    )

    print(
        f"Target Role: {target_role}"
    )

    print(
        f"\nResume Match Score: "
        f"{resume_score}/100"
    )

    print(
        f"Interview Score: "
        f"{interview_score}/100"
    )

    print(
        f"Final Hiring Score: "
        f"{final_score}/100"
    )

    print(
        f"Decision Confidence: "
        f"{confidence}/100"
    )

    print(
        f"\nFinal Recommendation: "
        f"{recommendation}"
    )

    print(
        f"Risk Level: "
        f"{risk_level}"
    )

    print(
        f"Next Action: "
        f"{next_action}"
    )

    print(
        "\n📁 Full report saved to:"
    )

    print(
        output_file
    )

    print(
        "\n🎉 AGENT 7 COMPLETED SUCCESSFULLY!"
    )


if __name__ == "__main__":

    test_hiring_report()