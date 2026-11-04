import json
import os

from agents.resume_parser.pdf_reader import (
    extract_resume_text
)

from agents.resume_parser.parser import (
    parse_resume
)

from agents.jd_parser.parser import (
    parse_job_description
)

from agents.resume_matcher.parser import (
    match_resume
)

from agents.skill_gap.parser import (
    analyze_skill_gap
)

from agents.interview_generator.parser import (
    generate_interview
)


class HiringPipeline:
    """
    Runs OptHire Agents 1 to 5 in sequence.

    Agent 1:
        Resume Parser

    Agent 2:
        Job Description Parser

    Agent 3:
        Resume Matcher

    Agent 4:
        Skill Gap Analyzer

    Agent 5:
        Interview Generator
    """

    def __init__(
        self,
        output_directory: str = "outputs"
    ):
        self.output_directory = (
            output_directory
        )

        os.makedirs(
            self.output_directory,
            exist_ok=True
        )

    def save_json(
        self,
        filename: str,
        data: dict
    ) -> str:
        """
        Saves an agent result to the
        output directory.
        """

        file_path = os.path.join(
            self.output_directory,
            filename
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

        return file_path

    def run(
        self,
        resume_path: str,
        job_description: str
    ) -> dict:
        """
        Runs Agents 1 to 5.

        Parameters:
            resume_path:
                Path to the candidate's
                resume PDF.

            job_description:
                Raw job description text.

        Returns:
            A dictionary containing all
            pipeline results.
        """

        print(
            "\n" + "=" * 60
        )

        print(
            "🚀 OPTHIRE AI HIRING PIPELINE"
        )

        print(
            "=" * 60
        )

        # ==================================
        # AGENT 1 — RESUME PARSER
        # ==================================

        print(
            "\n[1/5] 📄 Running "
            "Resume Parser..."
        )

        resume_text = extract_resume_text(
            resume_path
        )

        resume = parse_resume(
            resume_text
        )

        self.save_json(
            "parsed_resume.json",
            resume
        )

        print(
            "✅ Agent 1 completed"
        )

        # ==================================
        # AGENT 2 — JD PARSER
        # ==================================

        print(
            "\n[2/5] 💼 Running "
            "Job Description Parser..."
        )

        job = parse_job_description(
            job_description
        )

        self.save_json(
            "parsed_jd.json",
            job
        )

        print(
            "✅ Agent 2 completed"
        )

        # ==================================
        # AGENT 3 — RESUME MATCHER
        # ==================================

        print(
            "\n[3/5] 🎯 Running "
            "Resume Matcher..."
        )

        match_result = match_resume(
            resume,
            job
        )

        self.save_json(
            "match_result.json",
            match_result
        )

        print(
            "✅ Agent 3 completed"
        )

        # ==================================
        # AGENT 4 — SKILL GAP ANALYZER
        # ==================================

        print(
            "\n[4/5] 📈 Running "
            "Skill Gap Analyzer..."
        )

        skill_gap = analyze_skill_gap(
            resume,
            job,
            match_result
        )

        self.save_json(
            "skill_gap_report.json",
            skill_gap
        )

        print(
            "✅ Agent 4 completed"
        )

        # ==================================
        # AGENT 5 — INTERVIEW GENERATOR
        # ==================================

        print(
            "\n[5/5] 🎤 Running "
            "Interview Generator..."
        )

        interview = generate_interview(
            resume=resume,
            job_description=job,
            match_result=match_result,
            skill_gap=skill_gap
        )

        self.save_json(
            "interview_questions.json",
            interview
        )

        print(
            "✅ Agent 5 completed"
        )

        # ==================================
        # PIPELINE RESULT
        # ==================================

        result = {
            "status": "success",
            "resume": resume,
            "job_description": job,
            "match_result": match_result,
            "skill_gap": skill_gap,
            "interview": interview
        }

        print(
            "\n" + "=" * 60
        )

        print(
            "🎉 OPTHIRE ANALYSIS PIPELINE COMPLETED"
        )

        print(
            "=" * 60
        )

        print(
            "\nNext Step:"
        )

        print(
            "Candidate can now begin "
            "the AI interview."
        )

        return result