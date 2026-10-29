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

from google.cloud import bigquery
from google.oauth2 import service_account
from soar_sdk.exceptions import ActionFailure

from .asset import Asset


class LegacyFailure(ActionFailure):
    """Keep the legacy connectivity error message without an SDK prefix."""

    def __str__(self) -> str:
        return self.message


def credentials_and_project(asset: Asset):
    info = json.loads(asset.key_json)
    return service_account.Credentials.from_service_account_info(info), info["project_id"]


def create_client(asset: Asset) -> bigquery.Client:
    credentials, project = credentials_and_project(asset)
    return bigquery.Client(project=project, credentials=credentials)
