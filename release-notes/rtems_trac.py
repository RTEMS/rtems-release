#
# RTEMS Tools Project (http://www.rtems.org/)
# Copyright 2018 Danxue Huang (danxue.huang@gmail.com)
# Copyright 2022 Chris Johns (chris@contemporary.software)
# All rights reserved.
#
# This file is part of the RTEMS Tools package in 'rtems-tools'.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import codecs
import csv
import time

trac_base = 'https://devel.rtems.org'
ticket_base = trac_base + '/ticket'
format_rss = 'format=rss'
format_csv = 'format=csv'
query = 'query'
all_cols = [
    'id', 'summary', 'milestone', 'owner', 'type', 'status', 'priority',
    'component', 'version', 'severity', 'resolution', 'time', 'changetime',
    'blockedby', 'blocking', 'reporter', 'keywords', 'cc'
]
aggregate_cols = [
    'owner', 'type', 'priority', 'component', 'severity', 'reporter', 'version'
]


def gen_ticket_url(ticket_id):
    return ticket_base + '/' + str(ticket_id)


def gen_ticket_rss_url(ticket_id):
    return gen_ticket_url(ticket_id) + '?' + format_rss


def gen_ticket_csv_url(ticket_id):
    return gen_ticket_url(ticket_id) + '?' + format_csv


def gen_trac_query_csv_url(cols, **filters):
    return gen_trac_query_url(cols, **filters) + '&' + format_csv


def gen_attachment_link(attachment_name, ticket_number):
    return '/'.join([
        trac_base, 'attachment', 'ticket',
        str(ticket_number), attachment_name
    ])


def gen_trac_query_url(cols, **filters):
    constraints = []
    for col in cols:
        constraints.append('col={c}'.format(c=col))
    for key, value in filters.items():
        constraints.append('{k}={v}'.format(k=key, v=value))
    constraints_str = '&'.join(constraints)
    return trac_base + '/' + query + '?' + constraints_str


def open_ticket(ticket_id, cache, part='csv'):
    if part == 'csv':
        url = gen_ticket_csv_url(ticket_id)
    elif part == 'rss':
        url = gen_ticket_rss_url(ticket_id)
    else:
        raise RuntimeError('unknown part of ticket: ' + part)
    return cache.open_page(url)


def parse_csv_as_dict_iter(url, cache):
    csv_response = cache.open_page(url)
    return csv.DictReader(codecs.iterdecode(csv_response, 'utf-8-sig'))
