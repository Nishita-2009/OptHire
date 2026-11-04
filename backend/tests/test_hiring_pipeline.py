from orchestrator.hiring_pipeline import HiringPipeline


def test_hiring_pipeline():

    # Your resume PDF
    resume_path = "uploads/sample_resume.pdf"

    # Your sample job description
    jd_path = "uploads/sample_jd.txt"

    # Read the job description text
    with open(
        jd_path,
        "r",
        encoding="utf-8"
    ) as file:

        job_description = file.read()

    # Create the OptHire pipeline
    pipeline = HiringPipeline()

    # Run Agents 1 to 5 automatically
    result = pipeline.run(
        resume_path=resume_path,
        job_description=job_description
    )

    # Print final pipeline status
    print(
        "\nPipeline Status:",
        result["status"]
    )


if __name__ == "__main__":

    test_hiring_pipeline()