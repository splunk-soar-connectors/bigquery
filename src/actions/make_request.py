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
import json

import requests
from google.auth.transport.requests import AuthorizedSession
from soar_sdk.action_results import MakeRequestOutput
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import MakeRequestParams, Param

from ..asset import Asset
from ..client import credentials_and_project


BASE_URL = "https://bigquery.googleapis.com"
BIGQUERY_SCOPE = "https://www.googleapis.com/auth/bigquery"


class BigQueryMakeRequestParams(MakeRequestParams):
    endpoint: str = Param(
        description="BigQuery v2 path, for example /bigquery/v2/projects/my-project/datasets",
        required=True,
    )


def _endpoint(value: str) -> str:
    endpoint = value.strip()
    if not endpoint.startswith("/bigquery/v2/"):
        raise ActionFailure("Invalid endpoint: provide a BigQuery v2 path beginning with /bigquery/v2/")
    return endpoint


def _headers(value: str | None) -> dict[str, str]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if not value:
        return headers
    try:
        supplied = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ActionFailure("Invalid JSON headers") from exc
    if not isinstance(supplied, dict):
        raise ActionFailure("Invalid JSON headers")
    if any(key.lower() in {"authorization", "proxy-authorization", "host"} for key in supplied):
        raise ActionFailure("Authorization, Host, and Proxy-Authorization headers cannot be overridden")
    headers.update(supplied)
    return headers


def _query_parameters(value: str | None):
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        if value.lstrip().startswith("{"):
            raise ActionFailure("Invalid query parameters") from exc
        return value.lstrip("?")
    if not isinstance(parsed, dict):
        raise ActionFailure("Invalid query parameters: provide a JSON object or query string")
    return parsed


def _body(value: str | None):
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ActionFailure("Invalid JSON body") from exc


def make_request(params: BigQueryMakeRequestParams, asset: Asset) -> MakeRequestOutput:
    """Make an authenticated BigQuery v2 REST request with this asset's service account."""
    endpoint = _endpoint(params.endpoint)
    headers = _headers(params.headers)
    query_parameters = _query_parameters(params.query_parameters)
    json_body = _body(params.body)
    if params.timeout is not None and params.timeout <= 0:
        raise ActionFailure("Timeout must be greater than zero")

    try:
        credentials, _ = credentials_and_project(asset)
    except (KeyError, TypeError, ValueError) as exc:
        raise ActionFailure("Error creating client") from exc

    try:
        with AuthorizedSession(credentials.with_scopes([BIGQUERY_SCOPE])) as session:
            response = session.request(
                params.http_method,
                BASE_URL + endpoint,
                headers=headers,
                params=query_parameters,
                json=json_body,
                timeout=params.timeout or 30,
                verify=params.verify_ssl,
                allow_redirects=False,
            )
    except requests.RequestException as exc:
        raise ActionFailure(f"Request failed: {exc}") from exc

    return MakeRequestOutput(status_code=response.status_code, response_body=response.text)
