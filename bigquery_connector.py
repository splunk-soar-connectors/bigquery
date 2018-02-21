# --
# File: bigquery_connector.py
#
# Copyright (c) Phantom Cyber Corporation, 2018
#
# This unpublished material is proprietary to Phantom Cyber.
# All rights reserved. The methods and
# techniques described herein are considered trade secrets
# and/or confidential. Reproduction or distribution, in whole
# or in part, is forbidden except by express written permission
# of Phantom Cyber.
#
# --
# Phantom App imports
import phantom.app as phantom
from phantom.base_connector import BaseConnector
from phantom.action_result import ActionResult

# Usage of the consts file is recommended
# from bigquery_consts import *
import requests
import json

# "What's going on here?"
# Wheel files don't install how you expect (want?) them to if they would all go into the same directory
# For example, bigquery gets installed to google/cloud/bigquery, their auth gets installed to google/auth
# Pip wont be able to install these since they are all in the google directory (you'll need to use --upgrade, which will delete
#  the old files which were there). To  get around this, we can package all of the wheels in one wheel file.
# The problem with this is that each of Google's module's __init__.py have these two lines
#
#  from pkg_resources import get_distribution
#  __version__ = get_distribution('google-python-module-name').version
#
# This will throw an exception, because get_distribution isn't going to be able to find any of those modules
# This patch fixes that. Granted, every file is now going to be __version__ 1.0.0, but that shouldn't cause any problems

import pkg_resources


class VersionObj(object):  # noqa
    version = "1.0.0"      # noqa


_old_get_distribution = pkg_resources.get_distribution  # noqa


def _tmp_get_distribution(package_name):  # noqa
    return VersionObj()                   # noqa


pkg_resources.get_distribution = _tmp_get_distribution  # noqa

from google.oauth2 import service_account
from google.cloud import bigquery
# from google.cloud.exceptions import GoogleCloudError

pkg_resources.get_distribution = _old_get_distribution  # noqa

from concurrent.futures import TimeoutError


class RetVal(tuple):
    def __new__(cls, val1, val2):
        return tuple.__new__(RetVal, (val1, val2))


class BigQueryConnector(BaseConnector):

    def __init__(self):

        # Call the BaseConnectors init first
        super(BigQueryConnector, self).__init__()
        self._state = None

    def initialize(self):
        self._state = self.load_state()
        return phantom.APP_SUCCESS

    def finalize(self):
        self.save_state(self._state)
        return phantom.APP_SUCCESS

    def _create_client(self):
        config = self.get_config()
        service_account_json = json.loads(config['key_json'])

        credentials = service_account.Credentials.from_service_account_info(service_account_json)

        client = bigquery.Client(
            project=service_account_json['project_id'],
            credentials=credentials
        )

        return client

    def _handle_test_connectivity(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        self.save_progress("Creating BigQuery client...")
        try:
            client = self._create_client()
        except Exception as e:
            self.save_progress("Test Connectivity Failed")
            return action_result.set_status(phantom.APP_ERROR, "Error creating client", e)

        self.save_progress("Making test call to BigQuery...")
        try:
            client.list_datasets(max_results=1)
        except Exception as e:
            self.save_progress("Test Connectivity Failed")
            return action_result.set_status(phantom.APP_ERROR, "Error listing datasets", e)

        self.save_progress("Test Connectivity Passed")
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_list_tables(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        dataset = param.get('dataset')

        try:
            client = self._create_client()
        except Exception as e:
            return action_result.set_status(phantom.APP_ERROR, "Error creating client", e)

        if dataset:
            try:
                dataset_ref_list = [client.dataset(dataset)]
            except Exception as e:
                return action_result.set_status(phantom.APP_ERROR, "Unable to retrieved specified dataset", e)
        else:
            try:
                dataset_ref_list = [x.reference for x in client.list_datasets()]
            except Exception as e:
                return action_result.set_status(phantom.APP_ERROR, "Error creating a list of datasets", e)

        for dataset_ref in dataset_ref_list:
            for table in client.list_tables(dataset_ref):
                action_result.add_data({
                    'table_id': table.table_id,
                    'dataset_id': dataset_ref.dataset_id,
                    'project_id': dataset_ref.project,
                    'full_table_id': table.full_table_id,
                })

        action_result.update_summary({'total_tables': action_result.get_data_size()})

        return action_result.set_status(phantom.APP_SUCCESS, "Successfully listed tables")

    def _get_query_results(self, action_result, query_job, timeout):
        self.save_progress("Waiting for query results...")
        try:
            result = query_job.result(timeout=timeout)
        except TimeoutError:
            action_result.update_summary({
                'job_id': query_job.job_id
            })
            return action_result.set_status(phantom.APP_SUCCESS, "Timed out while waiting for results")
        except Exception as e:
            return action_result.set_status(phantom.APP_ERROR, "Error getting results from query", e)

        for row in result:
            action_result.add_data(dict(row))

        action_result.update_summary({
            'num_rows': action_result.get_data_size(),
        })

        return action_result.set_status(phantom.APP_SUCCESS, "Successfully retrieved results from Query")

    def _handle_get_results(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        job_id = param['job_id']
        timeout = param.get('timeout')
        if timeout:
            timeout = int(timeout)

        try:
            client = self._create_client()
        except Exception as e:
            return action_result.set_status(phantom.APP_ERROR, "Error creating client", e)

        query_job = client.get_job(job_id)

        return self._get_query_results(action_result, query_job, timeout)

    def _handle_run_query(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        query = param['query']
        timeout = param.get('timeout')
        if timeout:
            timeout = int(timeout)

        try:
            client = self._create_client()
        except Exception as e:
            return action_result.set_status(phantom.APP_ERROR, "Error creating client", e)

        query_job = client.query(query)

        return self._get_query_results(action_result, query_job, timeout)

    def handle_action(self, param):

        ret_val = phantom.APP_SUCCESS

        # Get the action that we are supposed to execute for this App Run
        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if action_id == 'test_connectivity':
            ret_val = self._handle_test_connectivity(param)

        elif action_id == 'get_results':
            ret_val = self._handle_get_results(param)

        elif action_id == 'list_tables':
            ret_val = self._handle_list_tables(param)

        elif action_id == 'run_query':
            ret_val = self._handle_run_query(param)

        return ret_val


if __name__ == '__main__':

    import sys
    import pudb
    import argparse

    pudb.set_trace()

    argparser = argparse.ArgumentParser()

    argparser.add_argument('input_test_json', help='Input Test JSON file')
    argparser.add_argument('-u', '--username', help='username', required=False)
    argparser.add_argument('-p', '--password', help='password', required=False)

    args = argparser.parse_args()
    session_id = None

    username = args.username
    password = args.password

    if (username is not None and password is None):

        # User specified a username but not a password, so ask
        import getpass
        password = getpass.getpass("Password: ")

    if (username and password):
        try:
            print ("Accessing the Login page")
            r = requests.get("https://127.0.0.1/login", verify=False)
            csrftoken = r.cookies['csrftoken']

            data = dict()
            data['username'] = username
            data['password'] = password
            data['csrfmiddlewaretoken'] = csrftoken

            headers = dict()
            headers['Cookie'] = 'csrftoken=' + csrftoken
            headers['Referer'] = 'https://127.0.0.1/login'

            print ("Logging into Platform to get the session id")
            r2 = requests.post("https://127.0.0.1/login", verify=False, data=data, headers=headers)
            session_id = r2.cookies['sessionid']
        except Exception as e:
            print ("Unable to get session id from the platfrom. Error: " + str(e))
            exit(1)

    if (len(sys.argv) < 2):
        print "No test json specified as input"
        exit(0)

    with open(sys.argv[1]) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))

        connector = BigQueryConnector()
        connector.print_progress_message = True

        if (session_id is not None):
            in_json['user_session_token'] = session_id

        ret_val = connector._handle_action(json.dumps(in_json), None)
        print (json.dumps(json.loads(ret_val), indent=4))

    exit(0)
