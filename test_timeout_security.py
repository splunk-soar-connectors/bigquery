# Copyright (c) 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from pathlib import Path


CONNECTOR_SOURCE = Path("bigquery_connector.py").read_text()


def test_query_result_timeout_reports_failure_and_preserves_job_id_guidance():
    timeout_handler = CONNECTOR_SOURCE.split("except TimeoutError:", 1)[1].split("except Exception", 1)[0]
    assert "phantom.APP_ERROR" in timeout_handler
    assert 'action_result.update_summary({"job_id": query_job.job_id})' in timeout_handler
    assert "use the get results action" in timeout_handler
