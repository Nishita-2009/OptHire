"""
Interview session workflow service.
Coordinates stateful candidate interview sessions with Agent 5 (Interview Generator),
Agent 6 (Interview Evaluator), and Agent 7 (Hiring Report Generator).
"""
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from database.models import Candidate, Job, AnalysisRun, InterviewSession, InterviewQuestion, InterviewAnswer
from database import repository
from agents.interview_generator import generate_interview
from agents.interview_evaluator import evaluate_answer, generate_final_interview_summary
from agents.hiring_report import generate_hiring_report

logger = logging.getLogger("opthire.interview_service")


class InterviewService:
    """Service orchestrating persistent interview session lifecycles."""

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
        summary_data = {}
        target_session_id = interview_session_id
        if not target_session_id:
            # Check if analysis has an interview session
            sessions = repository.list_interview_sessions(
                db, candidate_id=analysis.candidate_id, job_id=analysis.job_id
            )
            for s in sessions:
                if s.analysis_run_id == analysis_run_id and s.final_summary:
                    target_session_id = s.id
                    summary_data = s.final_summary
                    break
        else:
            session = repository.get_interview_session(db, target_session_id)
            if session and session.final_summary:
                summary_data = session.final_summary

        resume_data = analysis.resume_parse_result or (candidate.parsed_resume_data if candidate else {}) or {}
        job_data = analysis.job_parse_result or (job.parsed_job_data if job else {}) or {}
        match_data = analysis.match_result or {}
        skill_gap_data = analysis.skill_gap_result or {}

        logger.info("Generating final hiring report via Agent 7 for analysis %s", analysis_run_id)
        report = generate_hiring_report(
            resume=resume_data,
            job_description=job_data,
            match_result=match_data,
            skill_gap=skill_gap_data,
            interview_summary=summary_data,
        )

        final_decision = report.get("final_decision", {})
        recommendation = final_decision.get("recommendation", "Consider")
        scores = report.get("scores", {})
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
            "report_data": saved_report.report_data,
            "created_at": saved_report.created_at,
        }
