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
from soar_sdk.app import App

from ..views.query import display_query_results
from .get_results import GetResultsParams, QueryOutput, QuerySummary, get_results
from .list_tables import ListTablesOutput, ListTablesParams, ListTablesSummary, list_tables
from .make_request import make_request
from .run_query import RunQueryParams, run_query


def register_actions(app: App) -> None:
    app.register_action(
        action=list_tables,
        description="List Tables",
        action_type="investigate",
        read_only=True,
        params_class=ListTablesParams,
        output_class=ListTablesOutput,
        summary_type=ListTablesSummary,
        render_as="table",
    )
    for action, params, description, read_only in (
        (get_results, GetResultsParams, "Get results from a job started with 'run query'", True),
        (run_query, RunQueryParams, "Run a Query", False),
    ):
        app.action(
            description=description,
            action_type="investigate",
            read_only=read_only,
            params_class=params,
            output_class=QueryOutput,
            summary_type=QuerySummary,
            view_handler=display_query_results,
        )(action)
    app.make_request()(make_request)
