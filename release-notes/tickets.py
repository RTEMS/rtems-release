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

import html.entities
import html.parser
import os
import sys
import time
import threading

import xml.etree.ElementTree as ElementTree

import reraise
import rtems_trac
import trac


class rss_parser(html.parser.HTMLParser):

    def __init__(self, break_p=False):
        super(rss_parser, self).__init__()
        self.trace = False
        self.tags = []
        self.text = ''
        self.div_end = 0
        self.break_p = break_p

    def __del__(self):
        if self.trace:
            print('> del: ' + str(self))

    def __str__(self):
        o = ['text: ' + self.text]
        return os.linesep.join(o)

    def _clean_data(self, data):
        leading_ws = ' ' if len(data) > 0 and data[0].isspace() else ''
        trailing_ws = ' ' if len(data) > 0 and data[-1].isspace() else ''
        data = leading_ws + data.strip() + trailing_ws
        if self.break_p:
            data = data.replace(os.linesep, '<br />')
        return data

    def _tag_attr_get(self, attrs, key):
        if attrs:
            for attr, label in attrs:
                if attr == key:
                    return label
        return None

    def _tags_parse_all(self, start, tag, attrs, extended):
        if attrs and self.trace:
            for attr in attrs:
                print("     attr:", attr)
        o = ''
        if tag == 'em':
            o = '__'
        elif tag == 'strong':
            o = '__'
        elif tag == 'br':
            if self.div_end == 0 and not start:
                o = '<br />'
        elif tag == 'p':
            if self.div_end == 0:
                if start:
                    o = '<p>'
                else:
                    o = '</p>'
            else:
                o = os.linesep
        elif tag == 'div':
            if start:
                div_class = self._tag_attr_get(attrs, 'class')
                if div_class and self.div_end == 0:
                    o = os.linesep * 2 + '<div class="' + div_class + '">' + os.linesep
                    self.div_end += 1
                elif self.div_end > 0:
                    self.div_end += 1
            else:
                if self.div_end == 1:
                    o = os.linesep + '</div>' + os.linesep
                if self.div_end > 0:
                    self.div_end -= 1
            if self.trace:
                print(' tag: start = ', start, 'dev_end =', self.div_end)
        elif tag == 'ul' and extended:
            if start:
                o = '<ul>'
            else:
                o = '</ul>'
        elif tag == 'li' and extended:
            if start:
                o = '<li>'
            else:
                o = '</li>'
        elif tag == 'pre':
            if start:
                o = '<pre class="blockquote-code">'
            else:
                o = '</pre>'
        elif tag == 'blockquote':
            bq_class = self._tag_attr_get(attrs, 'class')
            if start:
                if bq_class:
                    o = '<blockquote class="' + bq_class + '">'
                else:
                    o = '<blockquote>'
            else:
                o = '</blockquote>'
        return o

    def _tags_parse_start(self, tag, attrs, extended=True):
        return self._tags_parse_all(True, tag, attrs, extended)

    def _tags_parse_end(self, tag, extended=True):
        return self._tags_parse_all(False, tag, None, extended)

    def _tags_push(self, tag):
        self.tags.append(tag)

    def _tags_pop(self, tag):
        if len(self.tags) != 0:
            self.tags.pop()

    def _tags_path(self):
        return '/'.join(self.tags)

    def _tags_in_path(self, path):
        return self._tags_path().startswith(path)

    def handle_starttag(self, tag, attrs):
        if self.trace:
            print("> start-tag (p):", tag)
        self._tags_push(tag)
        self.text += self._tags_parse_start(tag, attrs, True)

    def handle_endtag(self, tag):
        if self.trace:
            print("> end-tag (p):", tag)
        self._tags_pop(tag)
        self.text += self._tags_parse_end(tag)

    def handle_data(self, data):
        if self.trace:
            print("> data (p) :", data)
        data = self._clean_data(data)
        self.text += data


class rss_meta_parser(rss_parser):

    def __init__(self):
        super(rss_meta_parser, self).__init__()
        self.meta_data = []
        self.meta_steps = ['ul', 'li', 'strong']
        self.meta_label = None
        self.meta_text = ''

    def __str__(self):
        o = [
            'meta_data: %r' % (self.meta_data),
            'meta_label: ' + str(self.meta_label),
            'meta_text: ' + str(self.meta_text), 'text: ' + self.text
        ]
        return os.linesep.join(o)

    def _tags_metadata(self):
        return self.meta_label and self._tags_path().startswith('ul/li')

    def _tags_meta_label(self):
        return self._tags_path() == 'ul/li/strong'

    def handle_starttag(self, tag, attrs):
        if self.trace:
            print("> start-tag (m):", tag)
        in_metadata = self._tags_metadata()
        self._tags_push(tag)
        if self._tags_metadata():
            if in_metadata:
                self.meta_text += self._tags_parse_start(tag,
                                                         attrs,
                                                         extended=False)
        elif not self._tags_meta_label():
            self.text += self._tags_parse_start(tag, attrs, extended=False)

    def handle_endtag(self, tag):
        if self.trace:
            print("> end-tag (m):", tag)
        in_metadata = self._tags_metadata()
        self._tags_pop(tag)
        if in_metadata:
            # Trailing edge detect of the metadata end
            # Ignore the meta_label eng tag
            if not self._tags_metadata():
                self.meta_data.append(
                    (self.meta_label, self.meta_text.strip()))
                self.meta_label = None
                self.meta_text = ''
            elif len(self.meta_text) > 0:
                self.meta_text += self._tags_parse_end(tag, extended=False)
        else:
            self.text += self._tags_parse_end(tag, extended=False)

    def handle_data(self, data):
        if self.trace:
            print("> data (m) :", data)
        if not self.meta_label and self._tags_meta_label():
            self.meta_label = data.strip()
        elif self._tags_metadata():
            self.meta_text += self._clean_data(data)
        else:
            super(rss_meta_parser, self).handle_data(data)


class _ticket_fetcher(object):

    ns = {'dc': '{http://purl.org/dc/elements/1.1/}'}

    def __init__(self, ticket, cache):
        self.ticket = ticket
        self.cache = cache
        self.data = None
        self.thread = None
        self.result = None

    def _parse_ticket_csv(self):
        url = rtems_trac.gen_ticket_csv_url(self.ticket_id())
        csv_rows_iter = rtems_trac.parse_csv_as_dict_iter(url, self.cache)
        return dict(next(csv_rows_iter, {}))

    @staticmethod
    def dump_element(el, indent=0):
        if isinstance(el, ElementTree.Element):
            print('%stag:' % (' ' * indent), el.tag)
            print('%stext:' % (' ' * indent), len(el.text), el.text)
            print('%stail:' % (' ' * indent), len(el.tail), el.tail.strip())
            for item in el.items():
                _ticket_fetcher.dump_element(item, indent + 1)
        else:
            print('%sitem:' % (' ' * indent), el)

    def _item_text(self, item, break_p=False):
        if item is None:
            return None
        rp = rss_parser(break_p=break_p)
        if item.text:
            rp.feed(item.text)
        if item.tail:
            rp.feed(item.tail)
        return rp.text.strip()

    def _item_meta(self, item):
        title = item.find('title')
        creator = item.find(self.ns['dc'] + 'creator')
        author = item.find('author')
        if author is not None:
            creator = author
        pub_date = item.find('pubDate')
        guid = item.find('guid')
        description = item.find('description')
        category = item.find('category')
        if title.text is None:
            actions = 'comment'
        else:
            actions = title.text
        i = {
            'tag': self._item_tag(title.text),
            'actions': actions,
            'creator': self._item_text(creator),
            'published': self._item_text(pub_date),
            'guid': self._item_text(guid),
            'category': self._item_text(category)
        }
        rp = rss_meta_parser()
        rp.feed(description.text)
        rp.feed(description.tail)
        i['meta'] = rp.meta_data
        i['description'] = rp.text.strip()
        return i

    def _item_tag(self, tag):
        if tag is not None:
            ns = {'dc': '{http://purl.org/dc/elements/1.1/}'}
            if tag == ns['dc'] + 'creator':
                tag = 'creator'
            elif tag == 'pubData':
                tag = 'published'
            elif tag.startswith('attachment'):
                tag = 'attachment'
            elif tag.startswith('description'):
                tag = 'description'
            elif tag.startswith('milestone'):
                tag = 'milestone'
        else:
            tag = 'comment'
        return tag

    def _attachment_post(self, attachment):
        for m in range(0, len(attachment['meta'])):
            meta = attachment['meta'][m]
            if meta[0] == 'attachment' and \
               meta[1].startswith('set to __') and meta[1].endswith('__'):
                set_to_len = len('set to __')
                alink = meta[1][set_to_len:-2]
                meta = (meta[0],
                        meta[1][:set_to_len - 2] + \
                        '[' + alink + '](' + attachment['guid'] + '/' + alink + ')')
            attachment['meta'][m] = meta
        return attachment

    def _parse_ticket_rss(self):
        # Read xml data as ElementTree, and parse all tags
        ticket_rss = {}
        rss_response = rtems_trac.open_ticket(self.ticket_id(),
                                              self.cache,
                                              part='rss')
        rss_root = ElementTree.parse(rss_response).getroot()
        #
        # The channel has:
        #  title
        #  link
        #  description
        #  language
        #  image
        #  generator
        #  item
        #
        # The channel/item has:
        #  dc:creator
        #  author
        #  pubDate
        #  title
        #  link
        #  guid
        #  description
        #  category
        #
        channel = rss_root.find('channel')
        title = channel.find('title')
        link = channel.find('link')
        description = channel.find('description')
        items = channel.findall('item')
        citems = [self._item_meta(item) for item in items]
        ticket_rss['title'] = self._item_text(title)
        ticket_rss['link'] = self._item_text(link)
        ticket_rss['description'] = self._item_text(description, True)
        ticket_rss['attachments'] = \
            [self._attachment_post(ci) for ci in citems if 'comment' not in ci['guid']]
        ticket_rss['comments'] = \
            sorted([ci for ci in citems if 'comment' in ci['guid']],
                   key=lambda i: int(i['guid'][i['guid'].rfind(':') + 1:]))
        return ticket_rss

    def _runner(self):
        try:
            self.data = {
                'ticket': self.ticket,
                'meta': self._parse_ticket_csv(),
                'comment_attachment': self._parse_ticket_rss()
            }
        except KeyboardInterrupt:
            pass
        except:
            self.result = sys.exc_info()

    def ticket_id(self):
        return self.ticket['id']

    def run(self):
        self.thread = threading.Thread(target=self._runner,
                                       name='ticket-%s' % (self.ticket_id()))
        self.thread.start()

    def is_alive(self):
        return self.thread and self.thread.is_alive()

    def reraise(self):
        if self.result is not None:
            print()
            print('ticket:', self.ticket_id())
            reraise.reraise(*self.result)


class tickets:
    """This class load all tickets data for a milestone."""

    def __init__(self, release, milestone, cache=None):
        self.release = release
        self.milestone = milestone
        self.lock = threading.Lock()
        self.tickets = { 'release': release, 'milestone': milestone }

    def get_ticket_ids(self):
        return self.tickets.keys()

    def _fetch_data_for_ticket(self, ticket):
        return self._parse_ticket_data(ticket)

    def _job_waiter(self, jobs, num_jobs):
        while len(jobs) >= num_jobs:
            time.sleep(0.002)
            for job in jobs:
                if not job.is_alive():
                    job.reraise()
                    self.tickets['tickets'][job.data['meta']['id']] = job.data
                    self._update_stats(job.data)
                    jobs.remove(job)

    def load(self, cache, use_cache=False):
        if use_cache:
            tickets = cache.load()
            if tickets:
                self.tickets = tickets
                return
        # Read entire trac table as DictReader (iterator)
        self._pre_process_tickets_stats()
        tickets_reader = self._get_tickets_table_as_dict(cache)
        tickets = [t for t in tickets_reader]
        num_jobs = 20
        jobs = []
        job_count = 0
        job_total = len(tickets)
        job_len = len(str(job_total))
        for ticket in tickets:
            self._job_waiter(jobs, num_jobs)
            job = _ticket_fetcher(ticket, cache)
            jobs.append(job)
            job.run()
            job_count += 1
            print('\r %*d of %d - ticket %s ' %
                  (job_len, job_count, job_total, ticket['id']),
                  end='')
        self._job_waiter(jobs, 1)
        print()
        self._post_process_ticket_stats()
        cache.unload(self.tickets)

    def _update_stats(self, ticket):
        self.tickets['overall_progress']['total'] += 1
        if ticket['meta']['status'] == 'closed':
            self.tickets['overall_progress']['closed'] += 1
        if ticket['meta']['status'] == 'assigned':
            self.tickets['overall_progress']['assigned'] += 1
        if ticket['meta']['status'] == 'new':
            self.tickets['overall_progress']['new'] += 1
        for col in rtems_trac.aggregate_cols:
            col_value = ticket['meta'][col]
            self.tickets['by_category'][col][col_value] \
                = self.tickets['by_category'][col].get(col_value, {})
            if ticket['meta']['status'] == 'closed':
                self.tickets['by_category'][col][col_value]['closed'] \
                    = self.tickets['by_category'][col][col_value] \
                          .get('closed', 0) + 1
            self.tickets['by_category'][col][col_value]['total'] \
                = self.tickets['by_category'][col][col_value].get('total', 0) + 1

    def _pre_process_tickets_stats(self):
        self.tickets['overall_progress'] = {}
        self.tickets['by_category'] = {
            col: {}
            for col in rtems_trac.aggregate_cols
        }
        self.tickets['overall_progress']['total'] = 0
        self.tickets['overall_progress']['closed'] = 0
        self.tickets['overall_progress']['in_progress'] = 0
        self.tickets['overall_progress']['new'] = 0
        self.tickets['overall_progress']['assigned'] = 0
        self.tickets['tickets'] = {}

    def _post_process_ticket_stats(self):
        # (number of closed tickets) / (number of total tickets)
        n_closed = self.tickets['overall_progress'].get('closed', 0)
        n_total = self.tickets['overall_progress'].get('total', 0)
        self.tickets['overall_progress']['percentage'] \
            = "{0:.0%}".format((n_closed / n_total) if n_total > 0 else 0.0)
        # Get progress (closed/total) for each category
        for col in self.tickets['by_category']:
            for key in self.tickets['by_category'][col]:
                closed = self.tickets['by_category'][col][key].get('closed', 0)
                if closed == 0:
                    self.tickets['by_category'][col][key]['closed'] = 0
                total = self.tickets['by_category'][col][key].get('closed', 0)
                if total == 0:
                    self.tickets['by_category'][col][key]['total'] = 0
                self.tickets['by_category'][col][key]['progress'] \
                    = '{c}/{t}'.format(c=closed, t=total)

    def _get_tickets_table_as_dict(self, cache):
        csv_url = rtems_trac.gen_trac_query_csv_url(rtems_trac.all_cols,
                                                    milestone=self.milestone)
        return rtems_trac.parse_csv_as_dict_iter(csv_url, cache=cache)
