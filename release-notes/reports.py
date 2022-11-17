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

import datetime
import os
import re
import time
import threading
import sys

from markdown_generator import MarkdownGenerator
import reraise

heading_base = 2


class ticket(object):

    def __init__(self, fmt, ticket):
        self.generator = MarkdownGenerator()
        self.format = fmt
        self.ticket = ticket
        self.thread = None
        self.result = None

    def _format_contents(self):
        ticket_meta = self.ticket['meta']
        ticket_link = self.ticket.get('comment_attachment',
                                      {}).get('link', None)
        summary = ticket_meta.get('summary', None)
        ticket_meta.pop('description', None)
        ticket_meta.pop('summary', None)
        if ticket_link is not None:
            ticket_id_link = \
                self.generator.gen_hyperlink(self.ticket_id(), '#t' + self.ticket_id())
            tlink = self.generator.gen_bold(ticket_id_link) + \
                ' - ' + self.generator.gen_bold(summary)
            self.generator.gen_heading(tlink,
                                       heading_base + 1,
                                       anchor='t' + self.ticket_id())
        for k in ['Created', 'Modified', 'Blocked By']:
            ticket_meta[k] = self.ticket['ticket'][k]
        meta_keys = [k.capitalize() for k in ticket_meta.keys()]
        meta_vals = [v for v in ticket_meta.values()]
        order = [
            'Id', 'Reporter', 'Created', 'Modified', 'Owner', 'Type',
            'Component', 'Status', 'Resolution', 'Version', 'Milestone',
            'Priority', 'Severity', 'Keywords', 'Cc', 'Blocking', 'Blocked by'
        ]
        meta_table = []
        for c in range(0, len(order)):
            i = meta_keys.index(order[c])
            if meta_keys[i] in ['Created', 'Modified']:
                dt = datetime.datetime.strptime(meta_vals[i],
                                                '%m/%d/%y %H:%M:%S')
                ds = dt.strftime('%d %B %Y %H:%M:%S')
                if ds[0] == '0':
                    ds = ds[1:]
                meta_vals[i] = ds
            meta_table += [[
                self.generator.gen_bold(meta_keys[i]), meta_vals[i]
            ]]
        meta_table = [[
            self.generator.gen_bold('Link'),
            self.generator.gen_hyperlink(ticket_link, ticket_link)
        ]] + meta_table
        self.generator.gen_table(None, meta_table, align=['right', 'left'])

    def _description(self, description):
        description = description.replace('\r\n', '\n')

        #
        # The code blocks needs to be reviewed
        #
        if self.ticket_id() == '3384':
            description = re.sub('%s}}}', '%s}\n}\n}', description)

        if self.format == 'markdown':
            description = re.sub(r'{{{(.*)}}}', r'`\1`', description)
        else:
            description = re.sub(r'{{{(.*)}}}', r':code:`\1`', description)

        if self.format == 'rst':
            description = re.sub(r'(>+) ---', r'\1 \-\-\-', description)

        description = re.sub(r'{{{!(.*)\n', '{{{\n', description)
        description = re.sub(r'}}}}', '}\n}}}', description)
        description = re.sub(r'{{{[ \t]+\n', '{{{\n', description)
        description = re.sub(r'{{{([#$])', '{{{\n#', description)
        description = description.replace('{{{\n', '```\n')
        description = description.replace('\n}}}', '\n```')
        description = re.sub(
            r"^[ \t]*#([ \t]*define|[ \t]*include|[ \t]*endif|[ \t]*ifdef|" \
            "[ \t]*ifndef|[ \t]*if|[ \t]*else)(.*)$",
            r"`#\1\2`",
            description,
            flags=re.MULTILINE)

        if self.format == 'markdown':
            description = re.sub(r'{{{(?!\n)', '`', description)
            description = re.sub(r'(?!\n)}}}', '`', description)
        else:
            description = re.sub(r'{{{(?!\n)', ':code:`', description)
            description = re.sub(r'(?!\n)}}}', '`', description)

        # Two lines after the opening (and after the ending)
        # back-ticks misses up with the text area rendering.
        description = re.sub('```\n\n', '```\n', description)
        description = re.sub('\n\n```', '\n```', description)

        # For ticket 2624 where the opening three curly braces are not
        # on a separate line.
        description = re.sub(r'```(?!\n)', '```\n', description)
        description = re.sub(r'(?!\n)```', '\n```', description)

        # For ticket 2993 where the defective closing curly brackets
        # miss up with text area rendering.
        description = re.sub('}}:', '```\n', description)

        # Ticket 3771 has code that's not written in a code block,
        # which is interpretted by the Markdown generator as headers
        # (#define)... Hence, we fix that manually.

        if self.ticket_id() == '3771':
            description = re.sub('`#define',
                                 '```\n#define',
                                 description,
                                 count=1)
            description = re.sub('Problem facing on writing',
                                 '```\nProblem facing on writing',
                                 description,
                                 count=1)
            description = re.sub(r'[ ]{8,}', ' ', description)

        if self.format == 'rst':
            description = description.replace('=', '\\=')
            description = description.replace('\n', '\n\n')
            description = re.sub(r'^(#+)', '', description, flags=re.MULTILINE)

        return description

    def _format_description(self):
        if 'description' not in self.ticket['comment_attachment']:
            return
        description = self.ticket['comment_attachment']['description']
        self.generator.gen_raw_text(self.generator.gen_bold('Description'))
        self.generator.gen_line('')
        self.generator.gen_line_block(self._description(description))
        self.generator.gen_line('')

    def _meta_label(self, label):
        if label == 'attachment':
            label = 'attach'
        return label

    def _format_comments(self):
        if 'comments' not in self.ticket['comment_attachment']:
            return
        comments = self.ticket['comment_attachment']['comments']
        if len(comments) == 0:
            return
        self.generator.gen_line('')
        cnt = 0
        bold = self.generator.gen_bold
        for comment in comments:
            cnt += 1
            self.generator.gen_line(
                self.generator.gen_topic('Comment ' + str(cnt)))
            self.generator.gen_line('')
            if not comment['creator']:
                creator = 'none'
            else:
                creator = comment['creator']
            ul = [bold(creator) + ', ' + comment['published']]
            for m in comment['meta']:
                ul += [bold(self._meta_label(m[0]) + ':') + ' ' + m[1]]
            self.generator.gen_raw(self.generator.gen_ordered_lists(ul))
            self.generator.gen_line('')
            self.generator.gen_line_block(
                self._description(comment['description']))
            self.generator.gen_line('')

    def _format_attachments(self):
        if 'attachments' not in self.ticket['comment_attachment']:
            return
        attachments = self.ticket['comment_attachment']['attachments']
        if len(attachments) == 0:
            return
        self.generator.gen_heading('Attachments:', heading_base + 2)
        cnt = 0
        tab = []
        bold = self.generator.gen_bold
        for attachment in attachments:
            cnt += 1
            tab += [[
                bold(str(cnt)),
                bold('%s, %s' %
                     (attachment['creator'], attachment['published']))
            ]]
            for m in attachment['meta']:
                tab += [['', bold(self._meta_label(m[0])) + ': ' + m[1]]]
            if len(attachment['description']) != 0:
                tab += [['', attachment['description']]]
        if len(tab) != 0:
            self.generator.gen_line('')
            self.generator.gen_table(None, tab)
            self.generator.gen_line('')

    def _runner(self):
        try:
            self.formatter()
        except KeyboardInterrupt:
            pass
        except:
            self.result = sys.exc_info()

    def formatter(self):
        self._format_contents()
        self._format_description()
        self._format_attachments()
        self._format_comments()

    def ticket_id(self):
        return self.ticket['ticket']['id']

    def run(self):
        self.thread = threading.Thread(target=self._runner,
                                       name='format-ticket-%s' %
                                       (self.ticket_id()))
        self.thread.start()

    def is_alive(self):
        return self.thread and self.thread.is_alive()

    def reraise(self):
        if self.result is not None:
            reraise.reraise(*self.result)


class generator:

    def __init__(self, release, fmt='markdown'):
        if fmt != 'markdown' and fmt != 'trac':
            raise RuntimeError('invalid format: ' + fmt)
        self.release = release
        self.milestone = None
        self.format = fmt
        self.generator = MarkdownGenerator()

    def set_milestone(self, milestone):
        self.milestone = milestone

    def gen_toc(self, notes):
        headings = [line for line in notes
                    if line.startswith('##')] if notes is not None else []
        self.generator.gen_raw(self.md_toc(headings))

    def gen_start(self, notes):
        self.generator.gen_raw('# RTEMS Release ' + self.milestone +
                               os.linesep)
        if notes is not None:
            self.generator.gen_raw(os.linesep.join(notes))
        self.generator.gen_page_break()

    def gen_overall_progress(self, overall_progress):
        self.generator.gen_heading(
            'RTEMS ' + self.milestone + ' Ticket Overview', heading_base)
        self.generator.gen_table(
            [k.capitalize() for k in overall_progress.keys()],
            [overall_progress.values()],
            align='left')

    def gen_tickets_summary(self, tickets):
        self.generator.gen_line_break()
        self.generator.gen_heading(
            'RTEMS ' + self.milestone + ' Ticket Summary', heading_base)
        keys = tickets.keys()
        id_summary_mapping = [
            ('[%s](#t%s)' % (k, k), tickets[k]['meta']['status'],
             tickets[k]['meta']['summary']) for k in keys
        ]
        cols = ['ID', 'Status', 'Summary']
        self.generator.gen_table(cols, id_summary_mapping, sort_by='ID')
        self.generator.gen_line_break()

    @staticmethod
    def _convert_to_bulleted_link(name: str, generator):
        level = name.count('#')
        stripped_name = name.replace('#', '').strip()
        linked_name = name.lower().replace(' ',
                                           '-').replace('-', '', 1).replace(
                                               '#', '', level - 1)
        if not isinstance(generator, MarkdownGenerator):
            linked_name = linked_name.replace('.', '-')

        return f"{('    ' * (level - 1)) + '* '}[{stripped_name}]({linked_name})"

    def md_toc(self, headings):
        tmp_gen = MarkdownGenerator()
        toc_headers = [h[1:] for h in headings]
        toc_headers.extend([
            '# RTEMS ' + self.milestone + ' Ticket Overview',
            '# RTEMS ' + self.milestone + ' Ticket Summary',
            '# RTEMS ' + self.milestone + ' Tickets By Category'
        ])
        toc_headers.append('# RTEMS ' + self.milestone + ' Tickets')
        bulleted_links = []
        for c in toc_headers:
            bulleted_links.append(self._convert_to_bulleted_link(c, tmp_gen))
        for b in bulleted_links:
            tmp_gen.gen_unwrapped_line(b)
        return tmp_gen.content

    def gen_tickets_stats_by_category(self, by_category):
        self.generator.gen_heading('RTEMS ' + self.milestone + \
                                   ' Tickets By Category', heading_base)
        self.generator.gen_line('')

        for category in by_category:
            self.generator.gen_heading(category.capitalize(), heading_base + 1)

            # Get header and all rows to generate table, set category as first col
            header = [category.capitalize()]
            rows = []
            ticket_stats_list = list(by_category[category].values())
            if len(ticket_stats_list) > 0:
                header += [k.capitalize() for k in ticket_stats_list[0].keys()]

            for category_value in by_category[category]:
                ticket_stats = by_category[category][category_value]
                rows.append([category_value] + list(ticket_stats.values()))

            self.generator.gen_table(header, rows)
            self.generator.gen_line('')

    def gen_individual_tickets_info(self, tickets):
        self.generator.gen_line_break()
        self.generator.gen_heading('RTEMS ' + self.milestone + ' Tickets',
                                   heading_base)
        num_jobs = 1
        job_count = 0
        job_total = len(tickets)
        job_len = len(str(job_total))
        for ticket_id in sorted(list(tickets.keys())):
            job = ticket(self.format, tickets[ticket_id])
            job_count += 1
            print('\r %*d of %d - %s ticket %s ' %
                  (job_len, job_count, job_total, self.milestone, ticket_id),
                  end='')
            job.formatter()
            self.generator.gen_horizontal_line()
            self.generator.content += job.generator.content
        print()
