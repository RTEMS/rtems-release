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

import os
import re


class MarkdownGenerator:

    def __init__(self, line_width=78):
        self.content = ''
        self.line_width = line_width

    @staticmethod
    def _max_len(lst):
        max_len = 0
        for e in lst:
            if len(e) > max_len or (len(e) == 0 and max_len < len('&nbsp;')):
                max_len = len(e) if len(e) > 0 else len('&nbsp;')
        return max_len

    def gen_bullet_point(self, text):
        self.content += '* ' + self.wrap_line(
            self._convert_to_unicode_str(text), self.line_width) + os.linesep

    def gen_line(self, text):
        self.content += self.wrap_line(self._convert_to_unicode_str(text),
                                       self.line_width) + os.linesep

    def gen_unwrapped_line(self, text, is_raw_text=True):
        self.content += text
        self.content += ('  ' + os.linesep if is_raw_text else '<br />')

    def gen_heading(self, text, level, anchor=None):
        self.content += os.linesep + \
            '#' * level + ' ' + \
            self._convert_to_unicode_str(text)
        if anchor is not None:
            self.content += '      {#' + anchor + '}'
        self.content += os.linesep * 2

    def gen_wrapped_table(self, header, rows, max_num_cols=4):
        num_cols = len(header)
        i = 0
        if num_cols > max_num_cols:
            while i < num_cols:
                self.gen_table(
                    list(header)[i:i + max_num_cols],
                    [list(row)[i:i + max_num_cols] for row in rows],
                )
                self.gen_line(os.linesep)
                i += max_num_cols
        else:
            self.gen_table(header, rows, align='left')

    def gen_page_break(self):
        self.gen_line('')
        self.gen_line('')
        self.gen_line('<div class="new-page"></div>')
        self.gen_line('')

    def gen_line_break(self):
        self.gen_line('')
        self.gen_line('')
        self.gen_line('<br />')
        self.gen_line('')

    def gen_raw(self, content):
        self.content += content

    def gen_line_block(self, text):
        if len(text.strip()) > 0:
            self.content += os.linesep * 2 + '<div class="line-block">' + os.linesep
            self.content += text
            self.content += os.linesep * 2 + '</div>' + os.linesep
        return
        lines = text.split(os.linesep)
        code_block = False
        lb_lines = []
        for l in lines:
            if l.startswith('```'):
                code_block = not code_block
            else:
                if code_block:
                    lb_lines += ['    ' + l]
                else:
                    lb_lines += ['| ' + l]
        self.content += os.linesep + os.linesep.join(lb_lines) + os.linesep

    def gen_division_open(self, name):
        self.gen_line('')
        self.gen_line('<div class="%s">' % (name))
        self.gen_line('')

    def gen_division_close(self):
        self.gen_line('')
        self.gen_line('</div>')
        self.gen_line('')

    def gen_unordered_lists(self, items, level=0):
        md = []
        for i in items:
            if isinstance(i, list):
                md += self.gen_unordered_lists(i, level + 1)
            else:
                md += ['%s* %s' % (' ' * level, i)]
        return os.linesep.join(md)

    def gen_ordered_lists(self, items, level=0):
        md = []
        for i in items:
            if isinstance(i, list):
                md += self.gen_unordered_lists(i, level + 1)
            else:
                md += ['%s#. %s' % (' ' * level, i)]
        return os.linesep.join(md)

    def gen_table(self, header, rows, align='left', sort_by=None):
        rows = [[self._convert_to_unicode_str(r) for r in row] for row in rows]
        if header is None:
            cols = len(rows[0])
        else:
            header = [self._convert_to_unicode_str(h) for h in header]
            cols = len(header)
        if isinstance(align, str):
            align = [align] * cols
        else:
            if len(align) < cols:
                align += ['left'] * (cols - len(align))
        for c in range(0, len(align)):
            if align[c] not in ['left', 'right', 'center']:
                raise RuntimeError('invalid table alignment:' + a)
            align[c] = {
                'left': ('%-*s ', 1),
                'right': (' %*s', 1),
                'center': (' %-*s ', 2)
            }[align[c]]
        if isinstance(sort_by, str):
            if header is None:
                sort_by = None
            else:
                if sort_by not in header:
                    sort_by = None
                else:
                    sort_by = header.index(sort_by)
        if sort_by is None:
            sort_col = 0
        else:
            sort_col = sort_by
        ordered = [(k, i)
                   for i, k in enumerate([row[sort_col] for row in rows])]
        if sort_by is not None:
            ordered = sorted(ordered, key=lambda k: k[0])
        col_sizes = []
        if header is None:
            col_sizes = [0] * cols
        else:
            for hdr in header:
                col_sizes += [len(hdr)]
        for c in range(0, cols):
            col_max = self._max_len([row[c] for row in rows])
            if col_sizes[c] < col_max:
                col_sizes[c] = col_max
        line_len = 0
        for size in col_sizes:
            line_len += size
        line = []
        if header is not None:
            for c in range(0, cols):
                line += [align[c][0] % (col_sizes[c], header[c])]
        self.content += ' '.join(line) + os.linesep
        line = []
        for c in range(0, cols):
            line += ['-' * (col_sizes[c] + align[c][1])]
        table_line = ' '.join(line) + os.linesep
        self.content += table_line
        for o in ordered:
            row = rows[o[1]]
            line = []
            if len(col_sizes) != len(row):
                raise RuntimeError('header cols and row cols do not match')
            for c in range(0, len(row)):
                line += [
                    align[c][0] %
                    (col_sizes[c], row[c] if len(row[c]) > 0 else '&nbsp;')
                ]
            self.content += ' '.join(line) + os.linesep
        if header is None:
            self.content += table_line

    def gen_raw_text(self, formatted_text):
        self.content += os.linesep + formatted_text + os.linesep

    @staticmethod
    def gen_html_esc(text):
        for ch, esc in [('_', '&#95;'), ('*', '&#42')]:
            text = text.replace(ch, esc)
        return text

    @staticmethod
    def gen_anchor(text):
        return '[' + text + ']: #' + text + ' '

    @staticmethod
    def gen_bold(text):
        return '**' + MarkdownGenerator.gen_html_esc(text) + '**'

    @staticmethod
    def gen_topic(text):
        return '<div class="topic">' + os.linesep + text + os.linesep + '</div>'

    @staticmethod
    def gen_hyperlink(text, link):
        return '[' + text + ']' + '(' + link + ')'

    @staticmethod
    def wrap_line(line, width, is_raw_text=False):
        i = 0
        str_list = []
        while i < len(line):
            str_list.append(line[i:i + width])
            i += width
        return ('  \n' if is_raw_text else '<br />').join(str_list)

    def gen_horizontal_line(self):
        self.content += os.linesep + '--------' + os.linesep

    @staticmethod
    def _convert_to_unicode_str(text):
        try:
            return str(text)
        except UnicodeEncodeError:
            if isinstance(text, unicode):
                return text
            else:
                return unicode(text, "utf-8")
