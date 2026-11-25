#! /usr/bin/env python3
#
# RTEMS Tools Project (http://www.rtems.org/)
# Copyright 2020-2026 Chris Johns (chrisj@rtems.org)
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

import argparse
import re


def generate_readme(title, md_path, txt_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    ref_links = {}
    body_lines = []
    for line in raw.splitlines():
        m = re.match(r'^\s*\[([^\]]+)\]:\s*(\S+)\s*$', line)
        if m:
            ref_links[m.group(1).strip()] = m.group(2).strip()
        else:
            body_lines.append(line)

    def resolve_inline(text):

        def repl_ref(m):
            label, ref = m.group(1), m.group(2)
            target = ref_links.get(ref, ref)
            return target if label == target else f'{label} ({target})'

        text = re.sub(r'\[([^\]]+)\]\[([^\]]+)\]', repl_ref, text)

        def repl_inline(m):
            label, url = m.group(1), m.group(2)
            return url if label == url else f'{label} ({url})'

        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', repl_inline, text)

        text = re.sub(r'<(https?://[^>]+)>', r'\1', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        return text.rstrip()

    out_lines = [title, '=' * len(title), '']
    i = 0
    in_code = False

    while i < len(body_lines):
        line = body_lines[i]
        stripped = line.strip()

        if stripped.startswith('```') or stripped.startswith('~~~~'):
            in_code = not in_code
            i += 1
            continue

        if in_code:
            out_lines.append('    ' + line)
            i += 1
            continue

        if stripped == '---':
            out_lines.append('-' * 78)
            i += 1
            continue

        h_match = re.match(r'^(#{1,3})\s+(.+)$', stripped)
        if h_match:
            level = len(h_match.group(1))
            htext = resolve_inline(h_match.group(2))
            underline = '=' if level <= 2 else '-'
            out_lines.append('')
            out_lines.append(htext)
            out_lines.append(underline * len(htext))
            out_lines.append('')
            i += 1
            continue

        if '|' in line and not stripped.startswith('>'):
            table_block = []
            while i < len(body_lines) and '|' in body_lines[i]:
                table_block.append(body_lines[i])
                i += 1
            parsed_rows = []
            sep_idx = None
            for idx, trow in enumerate(table_block):
                cells = [c.strip() for c in trow.strip().strip('|').split('|')]
                if all(re.match(r'^:?-{2,}:?$', c) for c in cells if c):
                    sep_idx = idx
                    continue
                parsed_rows.append([resolve_inline(c) for c in cells])
            if parsed_rows:
                col_count = max(len(r) for r in parsed_rows)
                widths = [0] * col_count
                for r in parsed_rows:
                    for c_i, val in enumerate(r):
                        widths[c_i] = max(widths[c_i], len(val))
                for r_i, r in enumerate(parsed_rows):
                    padded = [
                        (r[c_i] if c_i < len(r) else '').ljust(widths[c_i])
                        for c_i in range(col_count)
                    ]
                    out_lines.append('  '.join(padded).rstrip())
                    if r_i == 0 and sep_idx == 1:
                        out_lines.append('  '.join('-' * w for w in widths))
                out_lines.append('')
            continue

        out_lines.append(resolve_inline(line))
        i += 1

    cleaned = []
    blank_run = 0
    for line in out_lines:
        if line.strip() == '':
            blank_run += 1
            if blank_run <= 1:
                cleaned.append('')
        else:
            blank_run = 0
            cleaned.append(line)

    with open(txt_path, 'w', encoding='utf-8') as out:
        out.write('\n'.join(cleaned).strip() + '\n')


def main():
    parser = argparse.ArgumentParser(
        description='Generate plain-text README.txt from assembled Markdown.')
    parser.add_argument('--title', required=True, help='Document title')
    parser.add_argument(
        '--markdown', required=True, help='Input assembled Markdown file')
    parser.add_argument('--output', required=True, help='Output README.txt path')
    args = parser.parse_args()
    generate_readme(args.title, args.markdown, args.output)


if __name__ == '__main__':
    main()
