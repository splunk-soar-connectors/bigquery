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
from pydantic import field_validator
from soar_sdk import logging
from soar_sdk.action_results import ActionResult
from soar_sdk.params import Param, Params

from ..asset import Asset
from ..client import create_client
from .get_results import _failure, _query_results


def _timeout(value):
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return 0
    return value if isinstance(value, float) and parsed > 0 else parsed


class RunQueryParams(Params):
    query: str = Param(
        description="Query to run",
        required=True,
        primary=True,
        cef_types=["bigquery query"],
    )
    timeout: float | None = Param(description="How long to wait for results", required=False)

    _parse_timeout = field_validator("timeout", mode="plain")(_timeout)


def run_query(params: RunQueryParams, asset: Asset):
    result = ActionResult(True, "", params.model_dump(exclude_unset=True))
    if params.timeout is not None and params.timeout <= 0:
        return _failure(result, "Please provide a positive integer in timeout")
    logging.progress("Running query...")
    try:
        client = create_client(asset)
    except Exception as exc:
        return _failure(result, "Error creating client", exc)

    job = client.query(params.query)
    return _query_results(result, job, params.timeout)
