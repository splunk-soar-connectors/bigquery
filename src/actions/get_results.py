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
from concurrent.futures import TimeoutError

from pydantic import field_validator
from soar_sdk import logging
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, ActionResult, OutputField, PermissiveActionOutput
from soar_sdk.params import Param, Params

from ..asset import Asset
from ..client import create_client


def _timeout(value):
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return 0
    return value if isinstance(value, float) and parsed > 0 else parsed


class GetResultsParams(Params):
    job_id: str = Param(
        description="Job ID",
        required=True,
        primary=True,
        cef_types=["bigquery job id"],
    )
    timeout: float | None = Param(description="How long to wait for results", required=False)

    _parse_timeout = field_validator("timeout", mode="plain")(_timeout)


class QueryOutput(PermissiveActionOutput):
    pass


class QuerySummary(ActionOutput):
    job_id: str | None = OutputField(cef_types=["bigquery job id"])
    num_rows: int | None


def _failure(
    params: Params,
    message: str,
    exc: Exception | None = None,
    job_id: str | None = None,
    rows: list[dict] | None = None,
) -> ActionResult:
    if exc is not None:
        message = f"{message}. Error string: '{exc}'"
    result = ActionResult(False, message, params.model_dump(exclude_unset=True))
    if job_id is not None:
        result.set_summary({"job_id": job_id})
    for row in rows or []:
        result.add_data(row)
    return result


def _query_results(params: Params, soar: SOARClient, job, timeout: int | float | None):
    logging.progress("Waiting for query results...")
    try:
        rows = job.result(timeout=timeout)
    except TimeoutError:
        return _failure(
            params,
            "Timed out while waiting for results; use the get results action with the returned job ID to continue polling",
            job_id=job.job_id,
        )
    except Exception as exc:
        return _failure(params, "Error getting results from query", exc, job.job_id)

    data = []
    try:
        data.extend(dict(row) for row in rows)
    except Exception as exc:
        return _failure(params, "Error processing query results", exc, job.job_id, data)

    soar.set_summary(QuerySummary(num_rows=len(data), job_id=job.job_id))
    soar.set_message("Successfully retrieved results from Query")
    return [QueryOutput(**row) for row in data]


def get_results(params: GetResultsParams, soar: SOARClient, asset: Asset):
    if params.timeout is not None and params.timeout <= 0:
        return _failure(params, "Please provide a positive integer in timeout")
    try:
        client = create_client(asset)
    except Exception as exc:
        return _failure(params, "Error creating client", exc)

    logging.progress("Fetching jobs...")
    try:
        job = client.get_job(params.job_id)
    except Exception as exc:
        return _failure(params, "Error fetching results", exc)
    return _query_results(params, soar, job, params.timeout)
