# --
# File: bigquery_view.py
#
# Copyright (c) 2018-2021 Splunk Inc.
#
# SPLUNK CONFIDENTIAL - Use or disclosure of this material in whole or in part
# without a valid written license from Splunk Inc. is PROHIBITED.
#
# --

from django.http import HttpResponse
import json


def display_query_results(provides, all_results, context):

    headers = []

    headers_set = set()
    for summary, action_results in all_results:
        for result in action_results:
            job_id = result.get_summary().get('job_id')
            if job_id is not None:
                headers = ['job_id']
                break
            header_data = result.get_data()
            if header_data:
                headers += header_data[0].keys()
                break

    if not headers_set:
        headers_set.update(headers)
    headers = sorted(headers_set)

    context['ajax'] = True
    if 'start' not in context['QS']:
        context['headers'] = headers
        return '/widgets/generic_table.html'

    start = int(context['QS']['start'][0])
    length = int(context['QS'].get('length', ['5'])[0])
    end = start + length
    # cur_pos = 0
    rows = []
    total = 0
    for summary, action_results in all_results:
        for result in action_results:
            job_id = result.get_summary().get('job_id')
            if job_id is not None:
                rows = [ [ {'value': job_id, 'contains': [ 'bigquery job id' ] } ] ]
                break
            data = result.get_data()
            total += len(data)
            for item in data[start:end]:
                row = []
                for h in headers:
                    row.append({ 'value': item.get(h) })
                rows.append(row)

    content = {
        "data": rows,
        "recordsTotal": total,
        "recordsFiltered": total,
    }

    return HttpResponse(json.dumps(content), content_type='text/javascript')
