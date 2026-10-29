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
import importlib
import json
from concurrent.futures import TimeoutError
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from soar_sdk.exceptions import ActionFailure

from src.actions.get_results import GetResultsParams, get_results
from src.actions.list_tables import ListTablesParams, list_tables
from src.actions.make_request import BigQueryMakeRequestParams, make_request
from src.actions.run_query import RunQueryParams, run_query
from src.app import app, test_connectivity as connectivity_action
from src.asset import Asset
from src.client import LegacyFailure, create_client
from src.views.query import display_query_results


@pytest.fixture
def asset():
    return Asset(key_json=json.dumps({"project_id": "test-project", "private_key": "not-a-real-key"}))


@pytest.fixture
def client(monkeypatch):
    mocked = MagicMock()
    for module_name in ("get_results", "list_tables", "run_query"):
        module = importlib.import_module(f"src.actions.{module_name}")
        monkeypatch.setattr(module, "create_client", lambda _asset: mocked)
    return mocked


def test_client_uses_asset_credentials_and_project(asset):
    credentials = object()
    with (
        patch("src.client.service_account.Credentials.from_service_account_info", return_value=credentials) as load,
        patch("src.client.bigquery.Client") as constructor,
    ):
        create_client(asset)
    load.assert_called_once_with(json.loads(asset.key_json))
    constructor.assert_called_once_with(project="test-project", credentials=credentials)


def test_connectivity_consumes_one_dataset_and_keeps_failure_messages(asset, monkeypatch):
    mocked = MagicMock()
    mocked.list_datasets.return_value = [SimpleNamespace(reference="one")]
    monkeypatch.setattr("src.app.create_client", lambda _asset: mocked)
    connectivity_action.__wrapped__(asset)
    mocked.list_datasets.assert_called_once_with(max_results=1)

    with patch.object(app, "_build_magic_args", return_value={"asset": asset}):
        app.actions_manager.get_action("test_connectivity")({})
    assert app.actions_manager.get_results()[-1].get_message() == ""

    mocked.list_datasets.side_effect = ValueError("permission denied")
    with pytest.raises(LegacyFailure, match="Error listing datasets"):
        connectivity_action.__wrapped__(asset)


def test_list_tables_preserves_rows_summary_and_dataset_selection(asset, client):
    dataset = SimpleNamespace(dataset_id="cases", project="test-project")
    table = SimpleNamespace(table_id="events", full_table_id="test-project:cases.events")
    client.dataset.return_value = dataset
    client.list_tables.return_value = [table]

    result = list_tables(ListTablesParams(dataset="cases"), asset)

    client.dataset.assert_called_once_with("cases")
    client.list_datasets.assert_not_called()
    assert result.get_data() == [
        {
            "table_id": "events",
            "dataset_id": "cases",
            "project_id": "test-project",
            "full_table_id": "test-project:cases.events",
        }
    ]
    assert result.get_summary() == {"total_tables": 1}
    assert result.get_message() == "Successfully listed tables"

    client.reset_mock()
    client.list_datasets.return_value = [SimpleNamespace(reference=dataset)]
    list_tables(ListTablesParams(dataset=""), asset)
    client.list_datasets.assert_called_once_with()
    client.list_tables.assert_called_once_with(dataset)


def test_query_rows_and_messages_are_preserved(asset, client):
    job = MagicMock(job_id="job-123")
    job.result.return_value = [{"z": 2, "a": "one"}, {"z": 3, "a": "two"}]
    client.query.return_value = job

    result = run_query(RunQueryParams(query="SELECT a, z", timeout="20"), asset)

    client.query.assert_called_once_with("SELECT a, z")
    job.result.assert_called_once_with(timeout=20)
    assert result.get_data() == [{"z": 2, "a": "one"}, {"z": 3, "a": "two"}]
    assert result.get_summary() == {"num_rows": 2, "job_id": "job-123"}
    assert result.get_message() == "Successfully retrieved results from Query"

    client.get_job.return_value = job
    result = get_results(GetResultsParams(job_id="job-123", timeout=20), asset)
    client.get_job.assert_called_once_with("job-123")
    job.result.assert_called_with(timeout=20)
    assert result.get_summary()["job_id"] == "job-123"


def test_timeout_result_keeps_job_id_in_sdk_action_result(asset, client):
    job = MagicMock(job_id="job-123")
    job.result.side_effect = TimeoutError
    client.query.return_value = job
    params = RunQueryParams(query="SELECT 1", timeout=1)

    result = run_query(params, asset)
    assert not result.get_status()
    assert result.get_summary() == {"job_id": "job-123"}
    assert result.get_message() == (
        "Timed out while waiting for results; use the get results action with the returned job ID to continue polling"
    )

    wrapped = app.actions_manager.get_action("run_query")
    with patch.object(app, "_build_magic_args", return_value={"asset": asset}):
        wrapped(params)
    assert app.actions_manager.get_results()[-1].get_summary() == {"job_id": "job-123"}


@pytest.mark.parametrize("timeout", [0, -1, "", "bad"])
def test_invalid_query_timeout_keeps_legacy_message(asset, client, timeout):
    for action, params in (
        (run_query, RunQueryParams(query="SELECT 1", timeout=timeout)),
        (get_results, GetResultsParams(job_id="job-123", timeout=timeout)),
    ):
        result = action(params, asset)
        assert not result.get_status()
        assert result.get_message() == "Please provide a positive integer in timeout"
    client.query.assert_not_called()
    client.get_job.assert_not_called()


def test_fractional_query_timeout_is_not_truncated(asset, client):
    job = MagicMock(job_id="job-123")
    job.result.return_value = []
    client.query.return_value = job
    client.get_job.return_value = job

    for action, params in (
        (run_query, RunQueryParams(query="SELECT 1", timeout=1.9)),
        (get_results, GetResultsParams(job_id="job-123", timeout=1.9)),
    ):
        job.result.reset_mock()
        result = action(params, asset)
        assert result.get_status()
        job.result.assert_called_once_with(timeout=1.9)


def test_empty_query_result_succeeds(asset, client):
    job = MagicMock(job_id="job-123")
    job.result.return_value = []
    client.query.return_value = job
    result = run_query(RunQueryParams(query="CREATE TABLE t (id INT64)"), asset)
    assert result.get_status()
    assert result.get_data() == []
    assert result.get_summary() == {"num_rows": 0, "job_id": "job-123"}


def test_query_widget_keeps_each_result_and_empty_state():
    first = SimpleNamespace(get_data=lambda: [{"z": "<safe>", "a": 1}])
    second = SimpleNamespace(get_data=lambda: [{"b": 2}])
    empty = SimpleNamespace(get_data=lambda: [])
    context = {}

    html = display_query_results(None, [(None, [first, second, empty])], context)

    assert [result["headers"] for result in context["results"]] == [["a", "z"], ["b"], []]
    assert html.count('<table class="phantom-table dataTable">') == 2
    assert "&lt;safe&gt;" in html
    assert "No data found" in html
    assert context["prerender"] is True


def test_make_request_returns_raw_api_error_and_keeps_auth_on_bigquery(asset):
    credentials = MagicMock()
    credentials.with_scopes.return_value = credentials
    session = MagicMock()
    session.__enter__.return_value = session
    session.request.return_value = SimpleNamespace(status_code=404, text='{"error":"missing"}')
    with (
        patch("src.actions.make_request.credentials_and_project", return_value=(credentials, "test-project")),
        patch("src.actions.make_request.AuthorizedSession", return_value=session),
    ):
        result = make_request(
            BigQueryMakeRequestParams(
                http_method="POST",
                endpoint="/bigquery/v2/projects/test-project/queries",
                headers='{"X-Test":"yes"}',
                query_parameters='{"dryRun":true}',
                body='{"query":"SELECT 1"}',
            ),
            asset,
        )
    credentials.with_scopes.assert_called_once_with(["https://www.googleapis.com/auth/bigquery"])
    assert result.status_code == 404
    assert result.response_body == '{"error":"missing"}'
    kwargs = session.request.call_args.kwargs
    assert session.request.call_args.args == ("POST", "https://bigquery.googleapis.com/bigquery/v2/projects/test-project/queries")
    assert kwargs["params"] == {"dryRun": True}
    assert kwargs["json"] == {"query": "SELECT 1"}
    assert kwargs["allow_redirects"] is False
    assert kwargs["verify"] is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"endpoint": "https://evil.example/bigquery/v2/projects/p/datasets"},
        {"endpoint": "//evil.example/bigquery/v2/projects/p/datasets"},
        {"endpoint": "/bigquery/v2/../admin"},
        {"headers": '{"Authorization":"Bearer other"}'},
        {"headers": "{"},
        {"query_parameters": "{bad"},
        {"body": "{bad"},
    ],
)
def test_make_request_rejects_invalid_inputs_before_network(asset, overrides):
    values = {"http_method": "GET", "endpoint": "/bigquery/v2/projects/p/datasets", **overrides}
    with patch("src.actions.make_request.AuthorizedSession") as session, pytest.raises(ActionFailure):
        make_request(BigQueryMakeRequestParams(**values), asset)
    session.assert_not_called()
