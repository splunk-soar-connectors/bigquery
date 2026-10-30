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
from soar_sdk.app import App

from .actions import register_actions
from .asset import Asset
from .client import LegacyFailure, create_client


app = App(
    name="Big Query",
    app_type="information",
    logo="logo_big_query.svg",
    logo_dark="logo_big_query_dark.svg",
    product_vendor="Google",
    product_name="Big Query",
    publisher="Splunk",
    appid="00eb093b-1864-460e-b1a9-c4156b735889",
    min_phantom_version="7.0.0",
    fips_compliant=True,
    asset_cls=Asset,
)


@app.test_connectivity()
def test_connectivity(asset: Asset) -> None:
    """Validate the asset configuration for connectivity using supplied configuration"""
    logging.progress("Creating BigQuery client...")
    try:
        client = create_client(asset)
    except Exception as exc:
        logging.progress("Test Connectivity Failed")
        raise LegacyFailure(f"Error creating client. Error string: '{exc}'") from exc

    logging.progress("Making test call to BigQuery...")
    try:
        [dataset.reference for dataset in client.list_datasets(max_results=1)]
    except Exception as exc:
        logging.progress("Test Connectivity Failed")
        raise LegacyFailure(f"Error listing datasets. Error string: '{exc}'") from exc

    logging.progress("Test Connectivity Passed")


def _legacy_connectivity_result(param=None):
    success = test_connectivity(param)
    if success:
        app.actions_manager.get_results()[-1].set_status(True, "")
    return success


_legacy_connectivity_result.meta = test_connectivity.meta
app.actions_manager.set_action("test_connectivity", _legacy_connectivity_result)


register_actions(app)


if __name__ == "__main__":
    app.cli()
