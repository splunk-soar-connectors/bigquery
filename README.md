# Big Query

Publisher: Splunk <br>
Connector Version: 2.1.9 <br>
Product Vendor: Google <br>
Product Name: Big Query <br>
Minimum Product Version: 7.0.0

This app allows running investigative actions against Google BigQuery

### Service Account

This app requires a pre-configured service account to operate. Please follow the procedure outlines
at [this link](https://support.google.com/a/answer/7378726?hl=en) to create a service account.\
The following API will need to be enabled:

- Bigquery API

At the end of the creation process, the admin console should ask you to save the config as a JSON
file. Copy the contents of the JSON file in the clipboard and paste it as the value of the "Contents
of Service Account JSON file" asset configuration parameter. Double check to make sure that the
"project_id" is the same project being used with BigQuery.

### Roles

Once the service account has been created, you will then need to give the account the correct role.
To do this, find "IAM & admin" on the menu to the left on the Google Cloud Console homepage. From
there, find your service account, and give it the role "Bigquery Admin".

### Make request

Use **make request** to call a BigQuery v2 REST endpoint with the service account configured on this asset. Enter a path beginning with `/bigquery/v2/`; the app sends it to `https://bigquery.googleapis.com`.

For example, use `GET` with `/bigquery/v2/projects/my-project/datasets` to list datasets, or `POST` with `/bigquery/v2/projects/my-project/queries` and a JSON body such as `{"query":"SELECT 1"}` to run a query. `headers` accepts a JSON object, `query_parameters` accepts a JSON object or query string, and `body` accepts JSON by default. The action returns the HTTP status code and raw response body, including BigQuery API error responses.

The SDK version of this app requires Python 3.13 or 3.14 and Splunk SOAR 7.0 or newer.

### Configuration variables

This table lists the configuration variables required to operate Big Query. These variables are specified when configuring a Big Query asset in Splunk SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**key_json** | required | password | Contents of Service Account JSON file |

### Supported Actions

[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration <br>
[list tables](#action-list-tables) - List Tables <br>
[get results](#action-get-results) - Get results from a job started with 'run query' <br>
[run query](#action-run-query) - Run a Query <br>
[make request](#action-make-request) - Make an authenticated BigQuery v2 REST request with this asset's service account.

## action: 'test connectivity'

Validate the asset configuration for connectivity using supplied configuration

Type: **test** <br>
Read only: **True**

Basic test for app.

#### Action Parameters

No parameters are required for this action

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'list tables'

List Tables

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**dataset** | optional | Only list tables in this dataset | string | `bigquery dataset` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.dataset | string | `bigquery dataset` | |
action_result.data.\*.dataset_id | string | `bigquery dataset` | company_dataset |
action_result.data.\*.table_id | string | | test_table_1 |
action_result.data.\*.full_table_id | string | | my-company-project-513002:company_dataset.test_table_1 |
action_result.data.\*.project_id | string | | my-company-project-513002 |
action_result.summary.total_tables | numeric | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'get results'

Get results from a job started with 'run query'

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**job_id** | required | Job ID | string | `bigquery job id` |
**timeout** | optional | How long to wait for results | numeric | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.job_id | string | `bigquery job id` | |
action_result.parameter.timeout | numeric | | |
action_result.data.\* | string | | |
action_result.summary.job_id | string | `bigquery job id` | |
action_result.summary.num_rows | numeric | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'run query'

Run a Query

Type: **investigate** <br>
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**query** | required | Query to run | string | `bigquery query` |
**timeout** | optional | How long to wait for results | numeric | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.query | string | `bigquery query` | |
action_result.parameter.timeout | numeric | | |
action_result.data.\* | string | | |
action_result.summary.job_id | string | `bigquery job id` | |
action_result.summary.num_rows | numeric | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'make request'

Make an authenticated BigQuery v2 REST request with this asset's service account.

Type: **generic** <br>
Read only: **False**

'make request' action for the app. Used to handle arbitrary HTTP requests with the app's asset

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**http_method** | required | The HTTP method to use for the request. | string | |
**endpoint** | required | BigQuery v2 path, for example /bigquery/v2/projects/my-project/datasets | string | |
**headers** | optional | The headers to send with the request (JSON object). An example is {'Content-Type': 'application/json'} | string | |
**query_parameters** | optional | Parameters to append to the URL (JSON object or query string). An example is ?key=value&key2=value2 | string | |
**body** | optional | The body to send with the request (JSON object). An example is {'key': 'value', 'key2': 'value2'} | string | |
**timeout** | optional | The timeout for the request in seconds. | numeric | |
**verify_ssl** | optional | Whether to verify the SSL certificate. | boolean | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.http_method | string | | |
action_result.parameter.endpoint | string | | |
action_result.parameter.headers | string | | |
action_result.parameter.query_parameters | string | | |
action_result.parameter.body | string | | |
action_result.parameter.timeout | numeric | | |
action_result.parameter.verify_ssl | boolean | | |
action_result.data.\*.status_code | numeric | | 200 404 500 |
action_result.data.\*.response_body | string | | {"key": "value"} |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

______________________________________________________________________

Auto-generated Splunk SOAR Connector documentation.

Copyright 2026 Splunk Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
