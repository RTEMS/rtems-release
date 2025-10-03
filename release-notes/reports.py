#
# RTEMS Tools Project (http://www.rtems.org/)
# Copyright 2024 Chris Johns (chris@contemporary.software)
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
import hashlib
import html.parser
import os
import re
import time
import sys
import urllib

from typing import Optional
from typing import Union


class url_meta:

    def __init__(self, project: dict, page_url: str) -> None:
        self.project = project
        self.page_url = page_url
        self.project_url = project['web_url']
        self.url = urllib.parse.urlsplit(self.project_url)
        self.host = urllib.parse.urlunparse(
            [self.url.scheme, self.url.netloc, '', '', '', ''])
        self.project_id_url = urllib.parse.urlunparse([
            self.url.scheme, self.url.netloc,
            '-/project/' + str(project['id']), '', '', ''
        ])
        self.project_path = self.url.path

    def __str__(self) -> str:
        out = []
        out += ['project_url = ' + str(self.project_url)]
        out += ['page_url = ' + str(self.page_url)]
        out += ['host = ' + self.host]
        out += ['project_path = ' + self.project_path]
        return os.linesep.join(out)

    def transform(self, link: str) -> str:
        us = urllib.parse.urlsplit(link)
        if us.scheme == '' or us.netloc == self.url.netloc:
            if link.startswith(self.host):
                pass
            elif link.startswith(self.project_path):
                link = urllib.parse.urljoin(self.host, link)
            elif link[0] in ['#']:
                link = urllib.parse.urljoin(self.page_url, link)
            elif us.netloc == '':
                ps = us.path.split('/')
                if len(ps) > 1:
                    if ps[1] in ['assets']:
                        if len(ps) > 2 and ps[2] == 'tracmigration':
                            link = self.project_url + '/-/blob/main' + link
                        else:
                            link = self.host + link
                    elif ps[1] in ['uploads']:
                        link = urllib.parse.urljoin(self.project_id_url,
                                                    link[1:])
        return link


class html_parser(html.parser.HTMLParser):

    def __init__(self, generator, url: url_meta) -> None:
        super().__init__()
        self.generator = generator
        self.url = url
        self.tag = None
        self.line = ''

    def write(self, text: str) -> None:
        if self.tag is not None:
            self.line += text
        else:
            self.generator.markdown(text, self.url)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == 'ul':
            self.tag = tag
        elif tag == 'li':
            self.write('* ')
        elif tag == 'code':
            self.write('``')
        elif tag in ['span', 'p']:
            pass
        else:
            raise RuntimeError('invalid html tag: ' + tag)

    def handle_endtag(self, tag):
        if tag == 'li':
            self.generator.write(self.line)
            self.line = ''
        elif tag == 'ul':
            self.tag = None
        elif tag == 'code':
            self.write('``')

    def handle_data(self, data):
        self.write(data)


class generator:

    md_comment_start = re.compile(r'<![-\S].*')
    md_comment_end = re.compile(r'.*[-\S]>')
    md_single_quote = re.compile(r'`(.*?)`')
    md_url = re.compile(r'\[([^\]]+)\]\([^)]+\)')
    md_reference = re.compile(r'[\s"]+[\w/]*[@!#][\w]+')
    md_unicode = re.compile(r'&#(.*?);')
    section_chars = ['*', '=', '-', '`', "'", '.', '~', '*', '+', '^']

    def __init__(self):
        super().__init__()
        self.md_trace = False
        self.milestone = None
        self.reset()

    def _heading(self, text: str, level: chr) -> None:
        self.write(text)
        self.write(level * len(text))
        self.write()

    def _anchor(self, ref: str) -> None:
        self.write('.. _' + ref + ':')
        self.write()

    def set_milestone(self, milestone):
        self.milestone = milestone

    def reset(self):
        self.out = []
        self.table = []
        self.indent_level = 0
        self.indent_stack = []
        self.write('.. RTEMS Release Note Generator. Do not edit')
        self.write()

    def write(self, line: Optional[Union[str, list]] = '') -> None:
        if isinstance(line, list):
            for l in line:
                self.write(l)
        else:
            self.out.append(' ' * self.indent_level + line)

    def output(self, out, fname):
        with open(os.path.join(out, fname) + '.rst', 'w') as f:
            f.write(os.linesep.join(self.out))

    def indent(self, level: int = 0) -> int:
        i = self.indent_level
        self.indent_level = level
        return i

    def indent_adjust(self, level: int, inc: bool = True) -> int:
        i = self.indent_level
        if inc:
            self.indent_level += level
        else:
            self.indent_level -= level
            if self.indent_level < 0:
                self.indent_level = 0
        return i

    def indent_push(self) -> int:
        self.indent_stack.append(self.indent_level)
        return self.indent_level

    def indent_pop(self) -> int:
        if len(self.indent_stack) > 0:
            self.indent_level = self.indent_stack.pop()
        return self.indent_level

    def block_break(self):
        self.write()
        self.write('..')
        self.write()

    def toc(self, caption: str, topics: list[str] = None) -> None:
        self.write('.. toctree::')
        self.write('   :maxdepth: 2')
        self.write('   :caption: ' + caption)
        self.write()
        if topics is not None:
            for topic in topics:
                self.write('   ' + topic)

    def milestone_start(self) -> None:
        l = 'RTEMS ' + self.milestone
        self.write(self.section_chars[0] * len(l))
        self.write(l)
        self.write(self.section_chars[0] * len(l))
        self.write()

    def project_heading(self, project: str) -> None:
        self._heading(project, self.section_chars[1])

    def group_heading(self, group: str) -> None:
        self._heading(group, self.section_chars[2])

    def issue_reference(self, issue: str, title: str) -> str:
        return 'rn-' + issue + '-' + str(
            int(hashlib.sha1(title.encode('utf-8')).hexdigest(), 16) % (10**8))

    def issue_heading(self, issue: str, title: str, state: str = None) -> None:
        s = issue + ' - ' + title
        if state is not None:
            s += ' (' + state + ')'
        self._anchor(self.issue_reference(issue, title))
        self._heading(s, self.section_chars[3])

    def heading(self, label: str) -> None:
        self._heading(label, self.section_chars[4])

    def detail(self, label: str, value: str) -> None:
        self.write('*' + label + '*' + ' ' + value)
        self.write()

    def link_test(self, detail: str, url: str) -> None:
        return '`' + detail + ' <' + url + '>`_'

    def link(self, detail: str, url: str) -> None:
        gen.write(self.link_test(detail, url))

    def divider(self) -> None:
        self.write()
        self.write('-' * 10)
        self.write()

    def table_start(self) -> None:
        self.table = [[]]

    def table_end_simple(self, heading: bool = False) -> None:
        cols = [len(r) for r in self.table]
        if len(set(cols)) != 1:
            raise RuntimeError('invalid table')
        cols = cols[0]
        col_len = 0
        for row in self.table:
            col_len = max([col_len] + [len(text) for text in row])

    def table_end(self,
                  mode='list',
                  heading: bool = False,
                  width: str = None,
                  widths: list[int] = None) -> None:
        cols = [len(r) for r in self.table]
        if len(set(cols)) != 1:
            raise RuntimeError('invalid table')
        cols = cols[0]
        if mode == 'simple':
            dashes = ''
            cols_len = [0] * cols
            for row in self.table:
                for col in range(0, cols):
                    if cols_len[col] < len(row[col]):
                        cols_len[col] = len(row[col])
            marker = '  '.join(['=' * l for l in cols_len])
            r_count = 0
            self.write(marker)
            for row in self.table:
                cols_text = []
                for col in range(0, cols):
                    cols_text += [
                        row[col] + ' ' * (cols_len[col] - len(row[col]))
                    ]
                self.write('  '.join(cols_text))
                if r_count == 0 and heading:
                    self.write(marker)
                r_count += 1
            self.write(marker)
        elif mode == 'list':
            self.write('.. list-table::')
            self.write('   :class: rrn-detail-table')
            self.write('   :align: left')
            if heading:
                self.write('   :header-rows: 1')
            if width is not None:
                self.write('   :width: ' + width)
            if widths is not None:
                self.write('   :widths: ' + ' '.join([w for w in widths]))
            self.write()
            for row in self.table:
                row_chr = '*'
                for text in row:
                    self.write('   ' + row_chr + ' - ' + text)
                    row_chr = ' '
        self.write()

    def table_row(self, last: bool = False) -> None:
        if not last:
            self.table.append([])

    def table_col(self,
                  text: Optional[Union[str, int, float]],
                  last: bool = False) -> None:
        if text is None:
            raise InvalidValue('table text is None')
        if isinstance(text, int) or isinstance(text, float):
            text = str(text)
        self.table[-1].append(text)

    def markdown(self, md: str, url: url_meta) -> None:

        def _filter_comments(line: str, in_comment: bool) -> None:
            process = True
            out = ''
            while process:
                process = False
                if in_comment:
                    m = generator.md_comment_end.match(line)
                    if m is not None:
                        line = line[m.span()[1]:]
                        in_comment = False
                        process = True
                if not in_comment:
                    if '<!-' in line:
                        m = generator.md_comment_start.match(line)
                        out += line[:m.span()[0]]
                        line_raw = line[m.span()[1]:]
                        in_comment = True
                        process = True
                    else:
                        out = line
            return in_comment, out

        def _unicode_filter(md: str, base: int):
            md = md.encode('ascii', 'xmlcharrefreplace').decode('utf-8')
            uchars = set(generator.md_unicode.findall(md))
            codes = {}
            for uc in uchars:
                code = '|md_' + str(base) + '_' + uc + '|'
                xml = '&#' + uc + ';'
                codes[code] = hex(int(uc))
                md = md.replace(xml, '\ ' + code + '\ ')
            return codes, md

        def _get_link(self, line: str, url: url_meta) -> None:
            m = generator.md_url.search(line)
            if m is not None:
                s = m.span()
                link = line[s[0]:s[1]]
                if self.md_trace:
                    print('link:', link)
                    print('m.group', m.group(0))
                url_end = link.rfind(')')
                link_end = link.find(']')
                link = link[1:link_end]
                if self.md_trace:
                    print(line, '||', link, s)
                    print(line[:s[1]])
                return link, line[:s[1]]
            return None, None

        def transform_url(self, line: str, url: url_meta) -> str:
            m = generator.md_url.search(line)
            if m is not None:
                s = m.span()
                link = line[s[0]:s[1]]
                if self.md_trace:
                    print('link:', link)
                    print('m.group', m.group(0))
                link_url_start = link.find('(') + 1
                link_url_end = link.rfind(')')
                link_url = link[link_url_start:link_url_end]
                if ' ' in link_url:
                    link_url_end = link.find('"')
                    link_url = link[link_url_start:link_url_end].strip()
                if self.md_trace:
                    print('line', line)
                    print('url:', url)
                    print('url_link:', link_url)
                    print('url.url:', url.url)
                link_url = url.transform(link_url)
                link_end = link.find(']')
                link = link[1:link_end]
                if link[0] in ['`', '*`']:
                    link = link[1:]
                if link[-1] in ['`', '*`']:
                    link = link[:-1]
                link_url = '`' + link + ' <' + link_url + '>`_'
                line = line[:s[0]] + link_url + line[s[1]:]
                if self.md_trace:
                    print(line, '[]', link, '[]', link_url)
            return line

        def transform_reference(self, line: str, url: url_meta) -> str:
            m = generator.md_reference.search(line)
            if m is not None:
                s = m.span()
                link_prefix = line[s[0]]
                link = line[s[0] + 1:s[1]].strip()
                link_num = link[1:]
                try:
                    num = int(link_num, 16)
                except:
                    link_num = None
                if link_num is not None:
                    l = generator.md_url.search(line)
                    if l is not None:
                        ls = l.span()
                        if self.md_trace:
                            print('l.group', l.group(0))
                            print('ls.span', ls)
                        if (s[0] < ls[0] or s[0] > ls[1]) and (s[1] < ls[0] or
                                                               s[1] > ls[1]):
                            link_num = None
                if link_num is not None:
                    if self.md_trace:
                        print('link:', link)
                        print('m.group', m.group(0))
                        print('m.span', s)
                    if '@' in link:
                        link_type = '@'
                        link_label = 'commit'
                    elif '#' in link:
                        link_type = '#'
                        link_label = 'issues'
                    elif '!' in link:
                        link_type = '!'
                        link_label = 'merge_requests'
                    ls = link.split(link_type)
                    if len(ls[0]) == 0:
                        ls[0] = url.project_path[1:]
                    link_url = url.host + '/' + ls[
                        0] + '/-/' + link_label + '/' + ls[1]
                    link_md = '[' + link + '](' + link_url + ')'
                    line = line[:s[0]] + link_prefix + link_md + line[s[1]:]
                    if self.md_trace:
                        print('link_type:', link_type, link_label)
                        print('link_url:', link_url)
                        print('link_md:', link_md)
                        print('line:', line)
            return line

        def write_line(self, line: str, url: url_meta) -> str:
            line = transform_reference(self, line, url)
            line = transform_url(self, line, url)
            return line

        if md is None:
            self.write()
            return

        self.indent_push()

        if self.md_trace:
            print('=' * 40)
            print(md)
            print('=' * 40)

        md = md.replace('\\', '\\\\')
        codes, md = _unicode_filter(md, 0)
        for code in codes:
            self.write('.. ' + code + ' unicode:: ' + codes[code] +
                       ' .. something')
        self.write()

        section_table = self.section_chars[4:]
        lines = md.split(os.linesep)
        block = 0
        section = 0
        table = None
        in_comment = False
        in_table = False
        in_code = False
        in_code_block = False
        line_out = ''
        reply_depth = 0
        for line in lines:
            in_comment, line = _filter_comments(line, in_comment)
            line = line.strip()
            if self.md_trace:
                print('-' * 40)
                print(line)
                print(' - ' * 40)
                print(line_out)
                print('-' * 40)
            if len(line) == 0:
                self.write()
                continue
            if line[0] == '>':
                depth = 0
                while len(line) != 0 and line[0] == '>':
                    depth += 1
                    line = line[1:].strip()
                if reply_depth != depth:
                    self.write()
                    self.indent_adjust(2 * (depth - reply_depth))
                    self.write()
                    reply_depth = depth
            else:
                reply_depth = 0
            while len(line) != 0:
                if in_code_block:
                    if '```' in line:
                        ls = line.split('```', 1)
                        self.write(ls[0])
                        self.indent_adjust(4, False)
                        if len(ls) > 1:
                            line = ls[1]
                        else:
                            line = ''
                        in_code_block = False
                    else:
                        self.write(line)
                        line = ''
                elif in_table:
                    if line[0] == '|':
                        rs = line.replace('||', '|').split('|')
                        if len(rs[0]) != 0 or len(rs[-1]) != 0:
                            in_table = False
                            self.write(write_line(self, line, url))
                        else:
                            table += [[rs[i] for i in range(1, len(rs) - 1)]]
                        line = ''
                    else:
                        self.table_start()
                        heading = False
                        add_row = False
                        first_row = True
                        for row in table:
                            if add_row:
                                self.table_row()
                            add_row = True
                            for col in row:
                                if col.startswith('---'):
                                    heading = True
                                    add_row = False
                                else:
                                    if first_row:
                                        if col[0] == '=':
                                            col = col[1:]
                                        if col[-1] == '=':
                                            col = col[:-1]
                                        col = col.strip()
                                    self.table_col(col)
                            first_row = False
                        self.table_row(True)
                        self.table_end(mode='simple', heading=heading)
                        in_table = False
                elif line[0] == '#':
                    this_block = 0
                    for i in range(0, len(line)):
                        if line[i] != '#':
                            break
                        this_block += 1
                    if this_block > block:
                        section += 1
                    elif this_block < block:
                        section -= 1
                    block = this_block
                    if section < 0:
                        section = 0
                    elif section >= len(section_table):
                        section = len(section_table)
                    line = line[this_block:].strip()
                    if len(line_out) != 0:
                        self.write(line_out)
                        line_out = ''
                    self.write()
                    self.write(write_line(self, line, url))
                    self.write(
                        write_line(self, section_table[section] * len(line),
                                   url))
                    self.write()
                    line = ''
                elif ('* ' == line[0:2]
                      or '- ' == line[0:2]) and len(line_out) == 0:
                    line_out += '* '
                    line = line[2:]
                elif '[ ] ' == line[0:4]:
                    line = line[4:]
                    line_out += '[] '
                elif '----' == line:
                    if len(line_out) != 0:
                        self.write(line_out)
                        line_out = ''
                    self.write()
                    self.write('-' * 10)
                    self.write()
                    line = ''
                elif line[0] == '|':
                    if not in_table:
                        table = []
                        in_table = True
                elif '\\\\' in line:
                    line = line.replace('\\\\', '\\')
                elif '```' in line:
                    ls = line.split('```', 1)
                    if len(ls) > 1:
                        cb_line = ls[1]
                    else:
                        cb_line = ''
                    code_block_type = ''
                    cbls = None
                    if len(cb_line) > 0:
                        if cb_line[0] != ' ':
                            cbls = cb_line.split(maxsplit=1)
                            code_block_type = ' ' + cbls[0]
                            if len(cbls) > 1:
                                ls[1] = cbls[1]
                            else:
                                ls[1] = ''
                    in_code_block = True
                    if len(line_out) != 0:
                        self.write(line_out)
                    line_out = write_line(self, ls[0], url)
                    self.write()
                    self.write('.. code-block::' + code_block_type)
                    self.indent_adjust(4)
                    self.write()
                    line = ls[1]
                elif '`' in line:
                    m = generator.md_single_quote.search(line)
                    if m is not None:
                        link, line_url = _get_link(self, line, url)
                        if link is not None:
                            s = m.span()
                            quoted = line[s[0]:s[1]]
                            if link == quoted:
                                line_out += write_line(self, line_url, url)
                                line = line[len(line_url):]
                                m = None
                        if m is not None:
                            line_out += write_line(self, line[:m.span()[0]],
                                                   url)
                            line_out += '`' + line[m.span()[0]:m.span(
                            )[1]] + '`'
                            line = line[m.span()[1]:]
                    else:
                        line_out += write_line(self, line, url)
                        line = ''
                else:
                    line_out += write_line(self, line, url)
                    line = ''
                if len(line) == 0 and len(line_out) != 0:
                    self.write(line_out)
                    line_out = ''

        self.write()
        self.indent_pop()

    def html(self, text: str, url: url_meta) -> None:
        html = html_parser(self, url)
        html.feed(text)
        self.write()
