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


def _failure(result: ActionResult, message: str, exc: Exception | None = None) -> ActionResult:
    if exc is not None:
        message = f"{message}. Error string: '{exc}'"
    result.set_status(False, message)
    return result


def list_tables(params: ListTablesParams, asset: Asset):
    result = ActionResult(True, "", params.model_dump(exclude_unset=True))
    try:
        client = create_client(asset)
    except Exception as exc:
        return _failure(result, "Error creating client", exc)

    logging.progress("Querying tables list...")
    if params.dataset:
        try:
            datasets = [client.dataset(params.dataset)]
        except Exception as exc:
            return _failure(result, "Unable to retrieve specified dataset", exc)
    else:
        try:
            datasets = [item.reference for item in client.list_datasets()]
        except Exception as exc:
            return _failure(result, "Error creating a list of datasets", exc)

    logging.progress("Processing tables list...")
    try:
        for dataset in datasets:
            for table in client.list_tables(dataset):
                result.add_data(
                    {
                        "table_id": table.table_id,
                        "dataset_id": dataset.dataset_id,
                        "project_id": dataset.project,
                        "full_table_id": table.full_table_id,
                    }
                )
    except Exception as exc:
        return _failure(result, "Error listing dataset", exc)

    result.set_summary({"total_tables": len(result.get_data())})
    result.set_status(True, "Successfully listed tables")
    return result
