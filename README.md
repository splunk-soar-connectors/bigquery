[comment]: # "Auto-generated SOAR connector documentation"
# Big Query

Publisher: Splunk  
Connector Version: 2\.0\.3  
Product Vendor: Google  
Product Name: Big Query  
Product Version Supported (regex): "\.\*"  
Minimum Product Version: 5\.0\.0  

This app allows running investigative actions against Google BigQuery

[comment]: # "    File: readme.md"
[comment]: # "    Copyright (c) 2018-2022 Splunk Inc."
[comment]: # ""
[comment]: # "Licensed under the Apache License, Version 2.0 (the 'License');"
[comment]: # "you may not use this file except in compliance with the License."
[comment]: # "You may obtain a copy of the License at"
[comment]: # ""
[comment]: # "    http://www.apache.org/licenses/LICENSE-2.0"
[comment]: # ""
[comment]: # "Unless required by applicable law or agreed to in writing, software distributed under"
[comment]: # "the License is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,"
[comment]: # "either express or implied. See the License for the specific language governing permissions"
[comment]: # "and limitations under the License."
[comment]: # ""
### Service Account

This app requires a pre-configured service account to operate. Please follow the procedure outlines
at [this link](https://support.google.com/a/answer/7378726?hl=en) to create a service account.  
The following API will need to be enabled:

-   Bigquery API

At the end of the creation process, the admin console should ask you to save the config as a JSON
file. Copy the contents of the JSON file in the clipboard and paste it as the value of the "Contents
of Service Account JSON file" asset configuration parameter. Double check to make sure that the
"project_id" is the same project being used with BigQuery.

### Roles

Once the service account has been created, you will then need to give the account the correct role.
To do this, find "IAM & admin" on the menu to the left on the Google Cloud Console homepage. From
there, find your service account, and give it the role "Bigquery Admin".

Package 'pyasn' has license 'MIT' with status 'needs revision'


### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Big Query asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**key\_json** |  required  | password | Contents of Service Account JSON file

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration  
[list tables](#action-list-tables) - List Tables  
[get results](#action-get-results) - Get results from a job started with 'run query'  
[run query](#action-run-query) - Run a Query  

## action: 'test connectivity'
Validate the asset configuration for connectivity using supplied configuration

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'list tables'
List Tables

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**dataset** |  optional  | Only list tables in this dataset | string |  `bigquery dataset` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.dataset | string |  `bigquery dataset` 
action\_result\.data\.\*\.dataset\_id | string |  `bigquery dataset` 
action\_result\.data\.\*\.full\_table\_id | string | 
action\_result\.data\.\*\.project\_id | string | 
action\_result\.data\.\*\.table\_id | string | 
action\_result\.summary\.total\_tables | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'get results'
Get results from a job started with 'run query'

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**job\_id** |  required  | Job ID | string |  `bigquery job id` 
**timeout** |  optional  | How long to wait for results | numeric | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.job\_id | string |  `bigquery job id` 
action\_result\.parameter\.timeout | numeric | 
action\_result\.data\.\* | string | 
action\_result\.summary\.job\_id | string |  `bigquery job id` 
action\_result\.summary\.num\_rows | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'run query'
Run a Query

Type: **investigate**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**query** |  required  | Query to run | string |  `bigquery query` 
**timeout** |  optional  | How long to wait for results | numeric | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.query | string |  `bigquery query` 
action\_result\.parameter\.timeout | numeric | 
action\_result\.data\.\* | string | 
action\_result\.summary\.job\_id | string |  `bigquery job id` 
action\_result\.summary\.num\_rows | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 