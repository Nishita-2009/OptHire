import os
from orchestrator.hiring_pipeline import HiringPipeline


def test_hiring_pipeline():
    candidate_resume_paths = [
        "uploads/sample_resume_synthetic.pdf",
        "uploads/sample_resume.pdf",
        "backend/uploads/sample_resume_synthetic.pdf",
        "backend/uploads/sample_resume.pdf",
    ]
    resume_path = None
    for p in candidate_resume_paths:
        if os.path.exists(p):
            resume_path = p
            break

    candidate_jd_paths = [
        "uploads/sample_jd.txt",
        "backend/uploads/sample_jd.txt",
    ]
    jd_path = None
    for p in candidate_jd_paths:
        if os.path.exists(p):
            jd_path = p
            break

    if not resume_path or not jd_path:
        raise FileNotFoundError("Sample inputs for hiring pipeline not found in uploads directory.")

    with open(jd_path, "r", encoding="utf-8") as file:
        job_description = file.read()

    pipeline = HiringPipeline()

    result = pipeline.run(
        resume_path=resume_path,
        job_description=job_description
    )

    print("\nPipeline Status:", result["status"])


if __name__ == "__main__":
    test_hiring_pipeline()
