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
    @classmethod
    def _to_json_schema(cls, parent_datapath="action_result.data.*", column_order_counter=None):
        yield {"data_path": parent_datapath, "data_type": "string"}


class QuerySummary(ActionOutput):
    job_id: str | None = OutputField(cef_types=["bigquery job id"])
    num_rows: int | None


def _failure(result: ActionResult, message: str, exc: Exception | None = None) -> ActionResult:
    if exc is not None:
        message = f"{message}. Error string: '{exc}'"
    result.set_status(False, message)
    return result


def _query_results(result: ActionResult, job, timeout: int | float | None) -> ActionResult:
    logging.progress("Waiting for query results...")
    try:
        rows = job.result(timeout=timeout)
    except TimeoutError:
        result.set_summary({"job_id": job.job_id})
        return _failure(
            result,
            "Timed out while waiting for results; use the get results action with the returned job ID to continue polling",
        )
    except Exception as exc:
        return _failure(result, "Error getting results from query", exc)

    try:
        for row in rows:
            result.add_data(dict(row))
    except Exception:
        pass  # Legacy behavior: queries without iterable rows still succeed.

    result.set_summary({"num_rows": len(result.get_data()), "job_id": job.job_id})
    result.set_status(True, "Successfully retrieved results from Query")
    return result


def get_results(params: GetResultsParams, asset: Asset):
    result = ActionResult(True, "", params.model_dump(exclude_unset=True))
    if params.timeout is not None and params.timeout <= 0:
        return _failure(result, "Please provide a positive integer in timeout")
    try:
        client = create_client(asset)
    except Exception as exc:
        return _failure(result, "Error creating client", exc)

    logging.progress("Fetching jobs...")
    try:
        job = client.get_job(params.job_id)
    except Exception as exc:
        return _failure(result, "Error fetching results", exc)
    return _query_results(result, job, params.timeout)
