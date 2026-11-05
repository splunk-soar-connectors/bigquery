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
from soar_sdk import logging
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, ActionResult, OutputField
from soar_sdk.params import Param, Params

from ..asset import Asset
from ..client import create_client


class ListTablesParams(Params):
    dataset: str | None = Param(
        description="Only list tables in this dataset",
        required=False,
        primary=True,
        cef_types=["bigquery dataset"],
    )


class ListTablesOutput(ActionOutput):
    dataset_id: str = OutputField(
        cef_types=["bigquery dataset"],
        column_name="Dataset",
        example_values=["company_dataset"],
    )
    table_id: str = OutputField(column_name="Table", example_values=["test_table_1"])
    full_table_id: str = OutputField(
        column_name="Full Table ID",
        example_values=["my-company-project-513002:company_dataset.test_table_1"],
    )
    project_id: str = OutputField(example_values=["my-company-project-513002"])


class ListTablesSummary(ActionOutput):
    total_tables: int


def _failure(
    params: ListTablesParams,
    message: str,
    exc: Exception | None = None,
    rows: list[dict] | None = None,
) -> ActionResult:
    if exc is not None:
        message = f"{message}. Error string: '{exc}'"
    result = ActionResult(False, message, params.model_dump(exclude_unset=True))
    for row in rows or []:
        result.add_data(row)
    return result


def list_tables(params: ListTablesParams, soar: SOARClient, asset: Asset):
    try:
        client = create_client(asset)
    except Exception as exc:
        return _failure(params, "Error creating client", exc)

    logging.progress("Querying tables list...")
    if params.dataset:
        try:
            datasets = [client.dataset(params.dataset)]
        except Exception as exc:
            return _failure(params, "Unable to retrieve specified dataset", exc)
    else:
        try:
            datasets = [item.reference for item in client.list_datasets()]
        except Exception as exc:
            return _failure(params, "Error creating a list of datasets", exc)

    logging.progress("Processing tables list...")
    rows = []
    try:
        for dataset in datasets:
            for table in client.list_tables(dataset):
                rows.append(
                    {
                        "table_id": table.table_id,
                        "dataset_id": dataset.dataset_id,
                        "project_id": dataset.project,
                        "full_table_id": table.full_table_id,
                    }
                )
    except Exception as exc:
        return _failure(params, "Error listing dataset", exc, rows)

    soar.set_summary(ListTablesSummary(total_tables=len(rows)))
    soar.set_message("Successfully listed tables")
    return [ListTablesOutput(**row) for row in rows]
