"""
Interview session workflow service.
Coordinates stateful candidate interview sessions with Agent 5 (Interview Generator),
Agent 6 (Interview Evaluator), and Agent 7 (Hiring Report Generator).
"""
import copy
import logging
import re
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.orm import Session

from database.models import Candidate, Job, AnalysisRun, InterviewSession, InterviewQuestion, InterviewAnswer
from database import repository
from agents.interview_generator import generate_interview
from agents.interview_evaluator import evaluate_answer, generate_final_interview_summary
from agents.hiring_report import generate_hiring_report

logger = logging.getLogger("opthire.interview_service")


GENERIC_ROLES = [
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Full-Stack Developer",
    "Software Engineer",
    "Software Developer",
    "Python Developer",
    "Web Developer",
    "Data Engineer",
]


class InterviewService:
    """Service orchestrating persistent interview session lifecycles."""

    @classmethod
    def clean_narrative_text(
        cls,
        text: str,
        candidate_name: Optional[str] = None,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        stale_titles: Optional[Set[str]] = None,
        stale_names: Optional[Set[str]] = None,
        stale_companies: Optional[Set[str]] = None,
        is_candidate_summary: bool = False,
        is_executive_summary: bool = False,
    ) -> str:
        """
        Deterministically sanitizes a narrative text snippet by replacing stale/conflicting
        job titles and candidate names with authoritative values while preserving phrasing and substance.
        """
        if not text or not isinstance(text, str):
            return text

        result = text
        stale_set = set(stale_titles or set())

        # If job_title is authoritative, replace stale or generic conflicting titles
        if job_title:
            candidates_to_replace = set(stale_set)
            for generic in GENERIC_ROLES:
                if generic.lower() != job_title.lower() and generic.lower() in result.lower():
                    if generic.lower() not in job_title.lower():
                        candidates_to_replace.add(generic)

            sorted_stale = sorted([s for s in candidates_to_replace if s and s.strip()], key=len, reverse=True)

            for stale in sorted_stale:
                if stale.lower() == job_title.lower():
                    continue

                # 1. Handle seniority prefixes (junior, senior, entry-level, intern, trainee, etc.)
                is_seniority_in_job = job_title.lower().startswith(
                    ("junior", "senior", "lead", "entry-level", "entry level", "intern", "trainee", "associate")
                )
                for p in ["entry-level", "entry level", "junior", "senior", "lead", "intern", "trainee", "associate"]:
                    pattern_prefix = re.compile(rf"\b{re.escape(p)}\s+{re.escape(stale)}\b", re.IGNORECASE)
                    if is_seniority_in_job:
                        result = pattern_prefix.sub(job_title, result)
                    else:
                        result = pattern_prefix.sub(f"{p} {job_title}", result)

                # 2. Handle plain stale title with boundary and substring protection
                if stale.lower() in job_title.lower():
                    idx = job_title.lower().find(stale.lower())
                    prefix = job_title[:idx].strip()
                    if prefix:
                        pattern_plain = re.compile(rf"(?<!{re.escape(prefix)}\s)\b{re.escape(stale)}\b", re.IGNORECASE)
                        result = pattern_plain.sub(job_title, result)
                    else:
                        suffix = job_title[idx + len(stale):].strip()
                        pattern_plain = re.compile(rf"\b{re.escape(stale)}\b(?!\s{re.escape(suffix)})", re.IGNORECASE)
                        result = pattern_plain.sub(job_title, result)
                else:
                    pattern_plain = re.compile(rf"\b{re.escape(stale)}\b", re.IGNORECASE)
                    result = pattern_plain.sub(job_title, result)

            # Ensure candidate_summary references authoritative job_title
            if is_candidate_summary and job_title.lower() not in result.lower():
                if result.lower().startswith("the candidate "):
                    result = f"For the {job_title} position, the candidate " + result[14:]
                else:
                    result = f"For the {job_title} position, {result}"

            # Ensure executive_summary references authoritative job_title
            if is_executive_summary and job_title.lower() not in result.lower():
                result = f"For the {job_title} role, {result}"

        # Handle candidate name
        if candidate_name:
            if stale_names:
                for sn in stale_names:
                    if sn and sn.lower() != candidate_name.lower():
                        pattern_sn = re.compile(rf"\b{re.escape(sn)}\b", re.IGNORECASE)
                        result = pattern_sn.sub(candidate_name, result)
            if is_executive_summary and result.startswith("The candidate "):
                result = candidate_name + " " + result[14:]

        # Handle company
        if company and stale_companies:
            for sc in stale_companies:
                if sc and sc.lower() != company.lower():
                    pattern_sc = re.compile(rf"\b{re.escape(sc)}\b", re.IGNORECASE)
                    result = pattern_sc.sub(company, result)

        return result

    @classmethod
    def harmonize_report_narratives(
        cls,
        report: Dict[str, Any],
        candidate_name: Optional[str] = None,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        stale_titles: Optional[Set[str]] = None,
        stale_names: Optional[Set[str]] = None,
        stale_companies: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """
        Deterministically harmonizes structured fields and narrative sections of a hiring report
        with authoritative database metadata (candidate_name, job_title, company), eliminating
        conflicting, stale, or generic titles from LLM outputs.
        """
        if not isinstance(report, dict):
            return report

        stale_titles = set(stale_titles or set())
        stale_names = set(stale_names or set())
        stale_companies = set(stale_companies or set())

        # Structured candidate section
        candidate_section = report.setdefault("candidate", {})
        if isinstance(candidate_section, dict):
            orig_name = candidate_section.get("name")
            if orig_name and candidate_name and orig_name.lower() != candidate_name.lower():
                stale_names.add(orig_name)
            if candidate_name:
                candidate_section["name"] = candidate_name

            orig_role = candidate_section.get("target_role")
            if orig_role and job_title and orig_role.lower() != job_title.lower():
                stale_titles.add(orig_role)
            if job_title:
                candidate_section["target_role"] = job_title

            if "candidate_summary" in candidate_section:
                candidate_section["candidate_summary"] = cls.clean_narrative_text(
                    candidate_section["candidate_summary"],
                    candidate_name=candidate_name,
                    job_title=job_title,
                    company=company,
                    stale_titles=stale_titles,
                    stale_names=stale_names,
                    stale_companies=stale_companies,
                    is_candidate_summary=True,
                )

        # Executive summary
        if "executive_summary" in report:
            report["executive_summary"] = cls.clean_narrative_text(
                report["executive_summary"],
                candidate_name=candidate_name,
                job_title=job_title,
                company=company,
                stale_titles=stale_titles,
                stale_names=stale_names,
                stale_companies=stale_companies,
                is_executive_summary=True,
            )

        # Resume evaluation section
        resume_sec = report.get("resume_evaluation")
        if isinstance(resume_sec, dict):
            if "summary" in resume_sec:
                resume_sec["summary"] = cls.clean_narrative_text(
                    resume_sec["summary"],
                    candidate_name=candidate_name,
                    job_title=job_title,
                    company=company,
                    stale_titles=stale_titles,
                    stale_names=stale_names,
                    stale_companies=stale_companies,
                )
            if "key_strengths" in resume_sec and isinstance(resume_sec["key_strengths"], list):
                resume_sec["key_strengths"] = [
                    cls.clean_narrative_text(
                        s,
                        candidate_name=candidate_name,
                        job_title=job_title,
                        company=company,
                        stale_titles=stale_titles,
                        stale_names=stale_names,
                        stale_companies=stale_companies,
                    )
                    for s in resume_sec["key_strengths"]
                ]
            if "key_weaknesses" in resume_sec and isinstance(resume_sec["key_weaknesses"], list):
                resume_sec["key_weaknesses"] = [
                    cls.clean_narrative_text(
                        s,
                        candidate_name=candidate_name,
                        job_title=job_title,
                        company=company,
                        stale_titles=stale_titles,
                        stale_names=stale_names,
                        stale_companies=stale_companies,
                    )
                    for s in resume_sec["key_weaknesses"]
                ]

        # Interview evaluation section
        interview_sec = report.get("interview_evaluation")
        if isinstance(interview_sec, dict) and "summary" in interview_sec:
            interview_sec["summary"] = cls.clean_narrative_text(
                interview_sec["summary"],
                candidate_name=candidate_name,
                job_title=job_title,
                company=company,
                stale_titles=stale_titles,
                stale_names=stale_names,
                stale_companies=stale_companies,
            )

        # Skill gap evaluation section
        skill_sec = report.get("skill_gap_evaluation")
        if isinstance(skill_sec, dict) and "development_summary" in skill_sec:
            skill_sec["development_summary"] = cls.clean_narrative_text(
                skill_sec["development_summary"],
                candidate_name=candidate_name,
                job_title=job_title,
                company=company,
                stale_titles=stale_titles,
                stale_names=stale_names,
                stale_companies=stale_companies,
            )

        # Final decision section
        decision_sec = report.get("final_decision")
        if isinstance(decision_sec, dict):
            for k in ["reasoning", "next_action"]:
                if k in decision_sec:
                    decision_sec[k] = cls.clean_narrative_text(
                        decision_sec[k],
                        candidate_name=candidate_name,
                        job_title=job_title,
                        company=company,
                        stale_titles=stale_titles,
                        stale_names=stale_names,
                        stale_companies=stale_companies,
                    )

        # Recruiter notes
        if "recruiter_notes" in report:
            report["recruiter_notes"] = cls.clean_narrative_text(
                report["recruiter_notes"],
                candidate_name=candidate_name,
                job_title=job_title,
                company=company,
                stale_titles=stale_titles,
                stale_names=stale_names,
                stale_companies=stale_companies,
            )

        # Key reasons lists
        for list_key in ["key_reasons_to_hire", "key_reasons_for_caution"]:
            if list_key in report and isinstance(report[list_key], list):
                report[list_key] = [
                    cls.clean_narrative_text(
                        s,
                        candidate_name=candidate_name,
                        job_title=job_title,
                        company=company,
                        stale_titles=stale_titles,
                        stale_names=stale_names,
                        stale_companies=stale_companies,
                    )
                    for s in report[list_key]
                ]

        return report

    @staticmethod
    def create_session(
        db: Session,
        candidate_id: str,
        job_id: str,
        analysis_run_id: Optional[str] = None,
        generate_questions: bool = True,
        custom_questions: Optional[List[Dict[str, Any]]] = None,
    ) -> InterviewSession:
        """
        Creates a new interview session.
        If generate_questions is True and candidate/job parsed data is present,
        calls Agent 5 to generate 21 personalized questions.
        """
        candidate = repository.get_candidate(db, candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found.")

        job = repository.get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        # Create base session
        session = repository.create_interview_session(
            db=db,
            candidate_id=candidate_id,
            job_id=job_id,
            analysis_run_id=analysis_run_id,
            status="pending",
        )

        questions_to_add: List[Dict[str, Any]] = []

        if custom_questions:
            questions_to_add = custom_questions
        elif generate_questions:
            # Gather analysis data if available
            match_data = {}
            skill_gap_data = {}
            if analysis_run_id:
                analysis = repository.get_analysis_run(db, analysis_run_id)
                if analysis:
                    match_data = analysis.match_result or {}
                    skill_gap_data = analysis.skill_gap_result or {}

            # Fallbacks if parsed data not present on models
            resume_data = candidate.parsed_resume_data or {"candidate_profile": candidate.full_name or "Candidate"}
            job_data = job.parsed_job_data or {"job_title": job.title, "description": job.description}

            logger.info("Generating interview questions via Agent 5 for session %s", session.id)
            generated = generate_interview(
                resume=resume_data,
                job_description=job_data,
                match_result=match_data,
                skill_gap=skill_gap_data,
            )

            # Flatten 21 questions from category buckets
            for cat_key, q_list in generated.items():
                if isinstance(q_list, list):
                    for q in q_list:
                        questions_to_add.append({
                            "id": q.get("question_id") or q.get("id"),
                            "question": q.get("question") or q.get("question_text", ""),
                            "category": q.get("category", cat_key),
                            "difficulty": q.get("difficulty", "medium"),
                            "purpose": q.get("purpose", ""),
                            "expected_points": q.get("expected_answer_points") or q.get("expected_points"),
                            "evaluation_criteria": q.get("evaluation_criteria"),
                        })

        if questions_to_add:
            repository.add_interview_questions(db, session.id, questions_to_add)
            # Re-fetch session with updated status and count
            session = repository.get_interview_session(db, session.id)

        return session

    @staticmethod
    def get_session_details(db: Session, session_id: str) -> Dict[str, Any]:
        """
        Retrieves full session status, questions, progress and completion status.
        """
        session = repository.get_interview_session(db, session_id)
        if not session:
            raise ValueError(f"Interview session {session_id} not found.")

        questions = repository.get_interview_questions(db, session_id)
        answers = repository.get_interview_answers(db, session_id)
        answered_question_ids = {ans.interview_question_id for ans in answers}

        questions_detail = []
        for q in questions:
            ans = next((a for a in answers if a.interview_question_id == q.id), None)
            questions_detail.append({
                "id": q.id,
                "sequence_number": q.sequence_number,
                "question_identifier": q.question_identifier,
                "question_text": q.question_text,
                "category": q.category,
                "difficulty": q.difficulty,
                "is_answered": q.id in answered_question_ids,
                "answer_text": ans.answer_text if ans else None,
                "score": ans.score if ans else None,
                "evaluation_result": ans.evaluation_result if ans else None,
            })

        # Determine current active question
        current_question = None
        for q in questions:
            if q.id not in answered_question_ids:
                current_question = {
                    "id": q.id,
                    "sequence_number": q.sequence_number,
                    "question_identifier": q.question_identifier,
                    "question_text": q.question_text,
                    "category": q.category,
                    "difficulty": q.difficulty,
                }
                break

        return {
            "session_id": session.id,
            "candidate_id": session.candidate_id,
            "job_id": session.job_id,
            "analysis_run_id": session.analysis_run_id,
            "status": session.status,
            "current_question_index": session.current_question_index,
            "total_questions": session.total_questions,
            "answered_questions_count": len(answers),
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "final_summary": session.final_summary,
            "current_question": current_question,
            "questions": questions_detail,
        }

    @staticmethod
    def submit_and_evaluate_answer(
        db: Session,
        session_id: str,
        question_id: str,
        answer_text: str,
    ) -> Dict[str, Any]:
        """
        Validates the session and question, submits candidate answer,
        evaluates via Agent 6, saves answer record, and advances progress.
        If all questions are answered, automatically triggers interview summary.
        """
        if not answer_text or not answer_text.strip():
            raise ValueError("Candidate answer text cannot be empty.")

        session = repository.get_interview_session(db, session_id)
        if not session:
            raise ValueError(f"Interview session {session_id} not found.")

        if session.status == "completed":
            raise ValueError(f"Interview session {session_id} is already completed.")

        question = repository.get_interview_question(db, question_id)
        if not question or question.interview_session_id != session_id:
            raise ValueError(f"Question {question_id} does not belong to session {session_id}.")

        # Check duplicate answer
        existing_answer = repository.get_answer_for_question(db, question_id)
        if existing_answer:
            raise ValueError(f"Question {question_id} has already been answered.")

        # Build payload for Agent 6 evaluation
        q_payload = {
            "question_id": question.question_identifier,
            "question": question.question_text,
            "category": question.category,
            "difficulty": question.difficulty,
            "expected_answer_points": question.expected_points or [],
            "evaluation_criteria": question.evaluation_criteria or {},
            "purpose": question.purpose or "",
        }

        logger.info("Evaluating answer for question %s via Agent 6", question.question_identifier)
        evaluation_result = evaluate_answer(
            question=q_payload,
            candidate_answer=answer_text.strip(),
        )

        # Extract score safely
        score = None
        if isinstance(evaluation_result, dict):
            raw_score = evaluation_result.get("score")
            if raw_score is not None:
                try:
                    score = float(raw_score)
                except (ValueError, TypeError):
                    score = None

        # Persist answer record
        answer = repository.save_interview_answer(
            db=db,
            question_id=question_id,
            answer_text=answer_text.strip(),
            evaluation_result=evaluation_result,
            score=score,
        )

        # Update session progress
        all_answers = repository.get_interview_answers(db, session_id)
        answered_count = len(all_answers)
        new_index = min(answered_count, session.total_questions)

        session = repository.update_interview_session_progress(
            db=db,
            session_id=session_id,
            current_question_index=new_index,
            status="in_progress",
        )

        # Auto-complete if all questions answered
        if session.total_questions > 0 and answered_count >= session.total_questions:
            session = InterviewService.finalize_interview_session(db, session_id)

        return {
            "session_id": session_id,
            "question_id": question_id,
            "answer_id": answer.id,
            "answer_text": answer.answer_text,
            "score": answer.score,
            "evaluation_result": answer.evaluation_result,
            "session_status": session.status,
            "current_question_index": session.current_question_index,
            "total_questions": session.total_questions,
            "is_interview_completed": session.status == "completed",
        }

    @staticmethod
    def finalize_interview_session(db: Session, session_id: str) -> InterviewSession:
        """
        Finalizes an interview session by aggregating all answer evaluations
        and generating a final interview summary with Agent 6.
        """
        session = repository.get_interview_session(db, session_id)
        if not session:
            raise ValueError(f"Interview session {session_id} not found.")

        answers = repository.get_interview_answers(db, session_id)
        if not answers:
            raise ValueError(f"Cannot complete session {session_id}: no answers have been submitted.")

        evaluations = [ans.evaluation_result for ans in answers if ans.evaluation_result]
        if not evaluations:
            # Fallback evaluation summary if empty
            evaluations = [
                {
                    "question_id": f"Q_{idx+1}",
                    "candidate_answer": ans.answer_text,
                    "score": ans.score or 0.0,
                    "feedback": "Answer recorded.",
                }
                for idx, ans in enumerate(answers)
            ]

        logger.info("Generating final interview summary via Agent 6 for session %s", session_id)
        summary = generate_final_interview_summary(evaluations)

        completed_session = repository.complete_interview_session(
            db=db,
            session_id=session_id,
            final_summary=summary,
        )
        return completed_session

    @staticmethod
    def generate_and_save_hiring_report(
        db: Session,
        analysis_run_id: str,
        interview_session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Coordinates generating a final hiring report via Agent 7
        using persisted candidate, job, analysis run, and interview session data.
        """
        analysis = repository.get_analysis_run(db, analysis_run_id)
        if not analysis:
            raise ValueError(f"Analysis run {analysis_run_id} not found.")

        candidate = repository.get_candidate(db, analysis.candidate_id)
        job = repository.get_job(db, analysis.job_id)

        # Retrieve session summary if provided or linked
        summary_data: Dict[str, Any] = {}
        target_session_id = interview_session_id
        is_provisional = False
        provisional_details: Dict[str, Any] = {}

        if not target_session_id:
            # Check if analysis has an interview session
            sessions = repository.list_interview_sessions(
                db, candidate_id=analysis.candidate_id, job_id=analysis.job_id
            )
            for s in sessions:
                if s.analysis_run_id == analysis_run_id:
                    target_session_id = s.id
                    break
            if not target_session_id and sessions:
                target_session_id = sessions[0].id

        if target_session_id:
            session = repository.get_interview_session(db, target_session_id)
            if session:
                if session.status == "completed" and session.final_summary:
                    # Completed session: use the stored final Agent 6 interview summary
                    summary_data = session.final_summary
                    is_provisional = False
                else:
                    # Incomplete session (pending or in_progress): evaluate submitted answers
                    answers = repository.get_interview_answers(db, target_session_id)
                    total_submitted = len(answers)
                    evaluated_answers = [
                        a for a in answers if a.evaluation_result is not None and a.score is not None
                    ]
                    evaluated_count = len(evaluated_answers)
                    valid_scores = [float(a.score) for a in evaluated_answers]
                    is_provisional = True

                    if total_submitted == 0:
                        # Explicit state: No answers submitted (Not Started)
                        summary_data = {
                            "overall_interview_score": 0,
                            "performance_level": "Not Started",
                            "status": "not_started",
                            "is_provisional": True,
                            "questions_answered": 0,
                            "total_questions": session.total_questions,
                            "evaluated_count": 0,
                            "interview_summary": (
                                f"Interview session ({session.id}) was generated with {session.total_questions} "
                                "questions, but candidate has not submitted any answers yet (Not Started)."
                            ),
                            "recommendation": "Consider",
                            "next_action": f"Candidate needs to start the interview session and answer the {session.total_questions} questions.",
                        }
                        provisional_details = {
                            "is_provisional": True,
                            "session_status": session.status,
                            "questions_answered": 0,
                            "total_questions": session.total_questions,
                            "evaluated_count": 0,
                            "partial_interview_score": 0.0,
                            "score_calculation": "No submitted answers; score set to 0.0.",
                        }
                    else:
                        # In-progress session with answers: calculate partial interview score
                        partial_score = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0.0
                        calc_explanation = (
                            f"Calculated as the arithmetic mean ({partial_score}/100) across {evaluated_count} "
                            f"validly evaluated answer(s) out of {total_submitted} submitted ({session.total_questions} total questions in rubric)."
                        )
                        summary_data = {
                            "overall_interview_score": partial_score,
                            "performance_level": f"Provisional ({total_submitted}/{session.total_questions} questions answered)",
                            "status": session.status,
                            "is_provisional": True,
                            "questions_answered": total_submitted,
                            "total_questions": session.total_questions,
                            "evaluated_count": evaluated_count,
                            "score_calculation": calc_explanation,
                            "interview_summary": (
                                f"Provisional interview evaluation: Candidate has answered {total_submitted} of "
                                f"{session.total_questions} questions ({evaluated_count} evaluated) with an average "
                                f"evaluated score of {partial_score}/100. This assessment is incomplete and provisional; "
                                "the interview session remains open."
                            ),
                            "evaluations_summary": [a.evaluation_result for a in evaluated_answers],
                            "recommendation": "Consider",
                            "next_action": f"Candidate should complete the remaining {session.total_questions - total_submitted} interview questions.",
                        }
                        provisional_details = {
                            "is_provisional": True,
                            "session_status": session.status,
                            "questions_answered": total_submitted,
                            "total_questions": session.total_questions,
                            "evaluated_count": evaluated_count,
                            "partial_interview_score": partial_score,
                            "score_calculation": calc_explanation,
                        }

        # Collect known stale / conflicting entity metadata
        stale_titles: Set[str] = set()
        stale_names: Set[str] = set()
        stale_companies: Set[str] = set()

        if candidate and candidate.full_name:
            if analysis.resume_parse_result:
                rn = analysis.resume_parse_result.get("name") or analysis.resume_parse_result.get("candidate_name")
                if rn and rn.lower() != candidate.full_name.lower():
                    stale_names.add(rn)
            if candidate.parsed_resume_data:
                rn = candidate.parsed_resume_data.get("name") or candidate.parsed_resume_data.get("candidate_name")
                if rn and rn.lower() != candidate.full_name.lower():
                    stale_names.add(rn)

        if job and job.title:
            if analysis.job_parse_result:
                jt = analysis.job_parse_result.get("job_title") or analysis.job_parse_result.get("title")
                if jt and jt.lower() != job.title.lower():
                    stale_titles.add(jt)
            if job.parsed_job_data:
                jt = job.parsed_job_data.get("job_title") or job.parsed_job_data.get("title")
                if jt and jt.lower() != job.title.lower():
                    stale_titles.add(jt)

        if job and job.company:
            if analysis.job_parse_result:
                jc = analysis.job_parse_result.get("company")
                if jc and jc.lower() != job.company.lower():
                    stale_companies.add(jc)
            if job.parsed_job_data:
                jc = job.parsed_job_data.get("company")
                if jc and jc.lower() != job.company.lower():
                    stale_companies.add(jc)

        # Authoritative entity metadata overrides stale or missing parsed JSON fields
        resume_data = dict(analysis.resume_parse_result or (candidate.parsed_resume_data if candidate else {}) or {})
        if candidate and candidate.full_name:
            resume_data["name"] = candidate.full_name
            resume_data["candidate_name"] = candidate.full_name

        job_data = dict(analysis.job_parse_result or (job.parsed_job_data if job else {}) or {})
        if job:
            if job.title:
                job_data["job_title"] = job.title
                job_data["title"] = job.title
            if job.company:
                job_data["company"] = job.company

        # Pre-clean match_data narrative fields so Agent 7 does not ingest conflicting titles
        match_data = copy.deepcopy(analysis.match_result or {})
        if match_data and job and job.title:
            for k in ["candidate_summary", "recommendation", "next_action"]:
                if k in match_data and isinstance(match_data[k], str):
                    match_data[k] = InterviewService.clean_narrative_text(
                        match_data[k],
                        candidate_name=candidate.full_name if candidate else None,
                        job_title=job.title,
                        company=job.company if job else None,
                        stale_titles=stale_titles,
                    )

        skill_gap_data = analysis.skill_gap_result or {}

        logger.info("Generating final hiring report via Agent 7 for analysis %s", analysis_run_id)
        report = generate_hiring_report(
            resume=resume_data,
            job_description=job_data,
            match_result=match_data,
            skill_gap=skill_gap_data,
            interview_summary=summary_data,
        )

        # Enforce authoritative database metadata on report output and narrative sections
        report = InterviewService.harmonize_report_narratives(
            report=report,
            candidate_name=candidate.full_name if (candidate and candidate.full_name) else None,
            job_title=job.title if (job and job.title) else None,
            company=job.company if (job and job.company) else None,
            stale_titles=stale_titles,
            stale_names=stale_names,
            stale_companies=stale_companies,
        )

        # Enforce provisional metadata & score adjustments on report output
        scores = report.setdefault("scores", {})
        if is_provisional:
            report["is_provisional"] = True
            report["provisional_details"] = provisional_details

            if provisional_details.get("questions_answered", 0) > 0:
                part_score = provisional_details.get("partial_interview_score", 0.0)
                scores["interview_score"] = part_score
                # In provisional reports, cap decision confidence appropriately
                curr_conf = scores.get("decision_confidence", 50)
                if curr_conf > 60:
                    scores["decision_confidence"] = 60
                if report.get("report_title") == "OptHire AI Hiring Report":
                    report["report_title"] = "OptHire AI Hiring Report (Provisional - In-Progress Interview)"
            else:
                scores["interview_score"] = 0.0
                if scores.get("decision_confidence", 50) > 50:
                    scores["decision_confidence"] = 50
        else:
            report["is_provisional"] = False

        final_decision = report.get("final_decision", {})
        recommendation = final_decision.get("recommendation", "Consider")
        overall_score = scores.get("final_hiring_score")

        saved_report = repository.create_hiring_report(
            db=db,
            analysis_run_id=analysis_run_id,
            report_data=report,
            recommendation=recommendation,
            overall_score=overall_score,
            interview_session_id=target_session_id,
        )

        return {
            "id": saved_report.id,
            "analysis_run_id": saved_report.analysis_run_id,
            "interview_session_id": saved_report.interview_session_id,
            "recommendation": saved_report.recommendation,
            "overall_score": saved_report.overall_score,
            "is_provisional": is_provisional,
            "report_data": saved_report.report_data,
            "created_at": saved_report.created_at,
        }

