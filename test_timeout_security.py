from pathlib import Path


CONNECTOR_SOURCE = Path("bigquery_connector.py").read_text()


def test_query_result_timeout_reports_failure_and_preserves_job_id_guidance():
    timeout_handler = CONNECTOR_SOURCE.split("except TimeoutError:", 1)[1].split("except Exception", 1)[0]
    assert "phantom.APP_ERROR" in timeout_handler
    assert 'action_result.update_summary({"job_id": query_job.job_id})' in timeout_handler
    assert "use the get results action" in timeout_handler
