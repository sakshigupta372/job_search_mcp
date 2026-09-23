from app import jobs


def test_search_jobs_by_keyword_and_location():
    result = jobs.search_jobs("AI Engineer", "Bangalore")
    assert result["success"] is True
    assert result["count"] >= 1
    titles = {job["title"] for job in result["jobs"]}
    assert "AI Engineer" in titles
    for job in result["jobs"]:
        assert "Bangalore" in job["location"]
        assert {"job_id", "title", "company", "location", "experience", "job_url"} <= job.keys()


def test_get_job_details():
    result = jobs.get_job_details("job-001")
    assert result["success"] is True
    job = result["job"]
    assert job["title"] == "AI Engineer"
    assert job["company"] == "Nimbus Labs"
    assert job["description"]
    assert job["requirements"]
    assert job["apply_url"]


def test_get_job_details_unknown_id():
    result = jobs.get_job_details("does-not-exist")
    assert result["success"] is False


def test_filter_jobs_by_experience_and_type():
    jobs.search_jobs("AI Engineer", "Bangalore")
    result = jobs.filter_jobs(experience="0-2", job_type="Full-time")
    assert result["success"] is True
    assert result["count"] >= 1
    for job in result["jobs"]:
        assert "0-2" in job["experience"]
        assert "Full-time" in job["job_type"]
