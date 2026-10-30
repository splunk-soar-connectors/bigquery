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
