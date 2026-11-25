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
import base64
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request

FALLBACK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 84" width="280" height="84">
  <defs>
    <linearGradient id="rtems-ring" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284c7"/>
      <stop offset="100%" stop-color="#0369a1"/>
    </linearGradient>
  </defs>
  <g transform="translate(8, 8)">
    <circle cx="34" cy="34" r="30" fill="none" stroke="url(#rtems-ring)" stroke-width="5"/>
    <ellipse cx="34" cy="34" rx="28" ry="11" transform="rotate(-28 34 34)" fill="none" stroke="#0ea5e9" stroke-width="2.5"/>
    <ellipse cx="34" cy="34" rx="28" ry="11" transform="rotate(28 34 34)" fill="none" stroke="#38bdf8" stroke-width="2.5"/>
    <circle cx="34" cy="34" r="7" fill="#0f172a"/>
    <circle cx="57" cy="21" r="3.5" fill="#0284c7"/>
    <circle cx="11" cy="47" r="3.5" fill="#0284c7"/>
  </g>
  <text x="84" y="45" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="34" font-weight="800" letter-spacing="2" fill="#0f172a">RTEMS</text>
  <text x="85" y="65" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" letter-spacing="1.4" fill="#475569">REAL-TIME EXECUTIVE</text>
</svg>"""


def encode_data_uri(raw_bytes, mime):
    b64 = base64.b64encode(raw_bytes).decode('ascii')
    return f'data:{mime};base64,{b64}'


def guess_mime(url, header_mime):
    clean_url = url.split('?')[0].split('#')[0].lower()
    if clean_url.endswith('.webp'):
        return 'image/webp'
    if clean_url.endswith('.ico'):
        return 'image/x-icon'
    if clean_url.endswith('.svg'):
        return 'image/svg+xml'
    if clean_url.endswith('.png'):
        return 'image/png'
    if header_mime and header_mime.startswith('image/'):
        return header_mime
    guessed, _ = mimetypes.guess_type(clean_url)
    return guessed or 'application/octet-stream'


def is_valid_image(raw_bytes, mime):
    if not raw_bytes or len(raw_bytes) < 32:
        return False
    head = raw_bytes[:256].lstrip().lower()
    if head.startswith(b'<!doctype') or head.startswith(b'<html'):
        return False
    return mime.startswith('image/')


def fetch_asset_as_data_uri(url, release_top, site_template, fallback_uri=''):
    if not url:
        return fallback_uri
    if url.startswith('data:'):
        return url

    basename = os.path.basename(url.split('?')[0].split('#')[0])
    if basename:
        search_dirs = (
            release_top,
            site_template,
            os.path.join(site_template, 'src', 'lib'),
            os.path.join(site_template, 'static'),
        )
        for folder in search_dirs:
            candidate = os.path.join(folder, basename)
            if folder and os.path.isfile(candidate):
                with open(candidate, 'rb') as f:
                    raw = f.read()
                mime = guess_mime(candidate, '')
                if is_valid_image(raw, mime):
                    return encode_data_uri(raw, mime)

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'
        ),
        'Accept': (
            'image/avif,image/webp,image/apng,image/svg+xml,'
            'image/*,*/*;q=0.8'
        ),
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            header_mime = (resp.headers.get_content_type() or '').lower()
            mime = guess_mime(url, header_mime)
            if is_valid_image(raw, mime):
                return encode_data_uri(raw, mime)
    except Exception:
        pass
    return fallback_uri or url


def build_payload(args):
    assets_cfg = {
        'faviconUrl': 'https://www.rtems.org/favicon.ico',
        'logoUrl': 'https://www.rtems.org/rtems.webp',
    }
    cfg_paths = (
        os.path.join(args.release_top, 'rtems-assets.json'),
        os.path.join(args.site_template, 'src', 'lib', 'rtems-assets.json'),
    )
    for cfg_path in cfg_paths:
        if cfg_path and os.path.isfile(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as cf:
                assets_cfg.update(json.load(cf))
            break

    fallback_svg_uri = encode_data_uri(
        FALLBACK_SVG.encode('utf-8'), 'image/svg+xml')
    logo_data_uri = fetch_asset_as_data_uri(
        assets_cfg.get('logoUrl', ''),
        args.release_top,
        args.site_template,
        fallback_svg_uri,
    )
    favicon_data_uri = fetch_asset_as_data_uri(
        assets_cfg.get('faviconUrl', ''),
        args.release_top,
        args.site_template,
        fallback_svg_uri,
    )

    with open(args.readme_base, 'r', encoding='utf-8') as f:
        markdown_body = f.read()

    markdown_body = (
        re.split(
            r'(?m)^##\s+Architectures and BSPs\b.*$',
            markdown_body,
            maxsplit=1,
        )[0].strip() + '\n'
    )
    markdown_body = re.sub(
        r'\[([^\]]+)\]\(file:///[^)]*\)', r'`\1`', markdown_body)
    markdown_body = re.sub(r'<file:///[^>]*>', '', markdown_body)

    with open(args.arch_bsp, 'r', encoding='utf-8') as f:
        arch_bsp_raw = f.read()

    summary_stats = {}
    architectures = []
    current_arch = None

    for raw_line in arch_bsp_raw.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        stat_match = re.match(r'^\*\*([^*:]+):\*\*\s*(.+)$', line)
        if stat_match:
            summary_stats[stat_match.group(1).strip()] = (
                stat_match.group(2).strip())
            continue

        if re.match(r'^-+\|-+$', line):
            continue

        if '|' in line:
            left, right = [part.strip() for part in line.split('|', 1)]
            if re.search(r'\bfamilies\s*:\s*\d+', right, re.I) or re.search(
                    r'\bbsps\s*:\s*\d+', right, re.I):
                current_arch = {
                    'arch': left,
                    'meta': re.sub(r'\s+', ' ', right),
                    'rows': [],
                }
                architectures.append(current_arch)
            elif current_arch is not None:
                current_arch['rows'].append({'bsp': left, 'family': right})

    return {
        'title': args.title,
        'release': args.release,
        'version': args.version,
        'revision': args.revision,
        'releaseUrl': args.release_url,
        'releaseNotes': args.release_notes,
        'date': args.date,
        'logoUrl': logo_data_uri,
        'faviconUrl': favicon_data_uri,
        'markdown': markdown_body,
        'archSummary': summary_stats,
        'architectures': architectures,
    }


def wrap_js_with_template_stack(js_code, max_len=2000):
    """JS-lexer-aware line wrapper & HTML tag escaper for inline <script>."""
    out = []
    line_len = 0
    n = len(js_code)
    i = 0

    state = 'code'
    template_brace_stack = []
    brace_depth = 0
    prev_non_ws = ''
    prev_word = ''
    word_buf = []

    regex_prev_tokens = set('(,=:[!&|?;{}~+-*%^<>')
    regex_prev_words = {
        'return',
        'throw',
        'case',
        'delete',
        'void',
        'typeof',
        'yield',
        'await',
        'in',
        'of',
        'instanceof',
        'else',
    }
    escape_lt_states = {'single', 'double', 'template', 'regex', 'regex_class'}

    def emit(ch):
        nonlocal line_len
        if ch == '<' and state in escape_lt_states:
            esc = r'\x3C'
        elif ord(ch) < 128:
            esc = ch
        else:
            esc = f'\\u{ord(ch):04x}'
        out.append(esc)
        if ch == '\n':
            line_len = 0
        else:
            line_len += len(esc)

    while i < n:
        ch = js_code[i]
        nxt = js_code[i + 1] if i + 1 < n else ''

        if state == 'code':
            if ch.isalnum() or ch in '_$':
                word_buf.append(ch)
                emit(ch)
                i += 1
                continue
            if word_buf:
                prev_word = ''.join(word_buf)
                prev_non_ws = prev_word[-1]
                word_buf = []

            if ch == '/' and nxt == '/':
                state = 'line_comment'
                emit(ch)
                emit(nxt)
                i += 2
                continue
            if ch == '/' and nxt == '*':
                state = 'block_comment'
                emit(ch)
                emit(nxt)
                i += 2
                continue
            if ch == "'":
                state = 'single'
                emit(ch)
                i += 1
                continue
            if ch == '"':
                state = 'double'
                emit(ch)
                i += 1
                continue
            if ch == '`':
                state = 'template'
                emit(ch)
                i += 1
                continue
            if ch == '/':
                if (prev_non_ws in regex_prev_tokens
                        or prev_word in regex_prev_words
                        or prev_non_ws == ''):
                    state = 'regex'
                    emit(ch)
                    i += 1
                    continue

            if ch == '{':
                brace_depth += 1
                emit(ch)
                prev_non_ws = ch
                prev_word = ''
                i += 1
                continue

            if ch == '}':
                emit(ch)
                prev_non_ws = ch
                prev_word = ''
                i += 1
                if (template_brace_stack
                        and brace_depth == template_brace_stack[-1]):
                    template_brace_stack.pop()
                    state = 'template'
                else:
                    brace_depth = max(0, brace_depth - 1)
                    if line_len >= max_len and not template_brace_stack:
                        emit('\n')
                continue

            emit(ch)
            if ch == ';' and line_len >= max_len and not template_brace_stack:
                emit('\n')
            if not ch.isspace():
                prev_non_ws = ch
                prev_word = ''
            i += 1

        elif state == 'single':
            emit(ch)
            if ch == '\\' and nxt:
                emit(nxt)
                i += 2
                continue
            if ch == "'":
                state = 'code'
                prev_non_ws = "'"
                prev_word = ''
            i += 1

        elif state == 'double':
            emit(ch)
            if ch == '\\' and nxt:
                emit(nxt)
                i += 2
                continue
            if ch == '"':
                state = 'code'
                prev_non_ws = '"'
                prev_word = ''
            i += 1

        elif state == 'template':
            if ch == '\\' and nxt:
                emit(ch)
                emit(nxt)
                i += 2
                continue
            if ch == '$' and nxt == '{':
                emit(ch)
                emit(nxt)
                template_brace_stack.append(brace_depth)
                state = 'code'
                prev_non_ws = '{'
                prev_word = ''
                i += 2
                continue
            emit(ch)
            if ch == '`':
                state = 'code'
                prev_non_ws = '`'
                prev_word = ''
            i += 1

        elif state == 'regex':
            emit(ch)
            if ch == '\\' and nxt:
                emit(nxt)
                i += 2
                continue
            if ch == '[':
                state = 'regex_class'
            elif ch == '/':
                state = 'code'
                prev_non_ws = '/'
                prev_word = ''
            i += 1

        elif state == 'regex_class':
            emit(ch)
            if ch == '\\' and nxt:
                emit(nxt)
                i += 2
                continue
            if ch == ']':
                state = 'regex'
            i += 1

        elif state == 'line_comment':
            emit(ch)
            if ch == '\n':
                state = 'code'
            i += 1

        elif state == 'block_comment':
            emit(ch)
            if ch == '*' and nxt == '/':
                emit(nxt)
                state = 'code'
                i += 2
                continue
            i += 1

    return ''.join(out)


def inject_and_finalize_html(built_html_path, payload, output_html_path):
    with open(built_html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    safe_json = (
        json.dumps(payload, indent=1, ensure_ascii=True).replace(
            '<', r'\u003c').replace('>', r'\u003e').replace('&', r'\u0026'))

    placeholder = (
        '<script id="rtems-release-data" type="application/json">{}</script>')
    replacement = (
        '<script id=\"rtems-release-data\" type=\"application/json\">\n'
        f'{safe_json}\n'
        '</script>'
    )

    if placeholder not in html:
        raise RuntimeError(
            'Could not find #rtems-release-data placeholder in built index.html'
        )

    html = html.replace(placeholder, replacement, 1)

    html = re.sub(
        r'<link\s+rel="icon"\s+href="https?://[^"]*"\s*/?>', '', html)
    favicon_uri = payload.get('faviconUrl', '')
    if favicon_uri:
        favicon_placeholder = (
            '<link id="rtems-favicon" rel="icon" href="data:," />')
        favicon_tag = (
            f'<link id="rtems-favicon" rel="icon" href="{favicon_uri}" />')
        if favicon_placeholder in html:
            html = html.replace(favicon_placeholder, favicon_tag, 1)
        elif '</head>' in html:
            html = html.replace('</head>', f'  {favicon_tag}\n  </head>', 1)

    script_open = '<script>\n\t\t\t\t{'
    script_close = '\n\t\t\t</script>'
    start_idx = html.rfind(script_open)
    end_idx = html.rfind(script_close)

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        js_start = start_idx + len('<script>')
        raw_js = html[js_start:end_idx]
        wrapped_js = wrap_js_with_template_stack(raw_js, max_len=2000)

        wrapped_js = re.sub(
            r'<(/?(?:script|head|body|html))(?=\s|>|/)',
            lambda m: r'\x3C' + m.group(1),
            wrapped_js,
            flags=re.IGNORECASE,
        )

        with tempfile.NamedTemporaryFile(
                'w', suffix='.js', encoding='utf-8', delete=True) as tmp_js:
            tmp_js.write(wrapped_js)
            tmp_js.flush()
            subprocess.run(['node', '--check', tmp_js.name], check=True)

        html = html[:js_start] + wrapped_js + html[end_idx:]

    with open(output_html_path, 'w', encoding='utf-8') as out:
        out.write(html)


def build_coverpage(args):
    if os.path.exists(args.build_dir):
        shutil.rmtree(args.build_dir)
    shutil.copytree(args.site_template, args.build_dir)

    stub_data_path = os.path.join(
        args.build_dir, 'src', 'lib', 'release-data.json')
    with open(stub_data_path, 'w', encoding='utf-8') as f:
        f.write('{"title":"RTEMS"}\n')

    payload = build_payload(args)

    lock_file = os.path.join(args.build_dir, 'package-lock.json')
    if os.path.isfile(lock_file):
        npm_install_cmd = ['npm', 'ci', '--include=dev', '--silent']
    else:
        npm_install_cmd = [
            'npm',
            'install',
            '--include=dev',
            '--no-audit',
            '--no-fund',
            '--silent',
        ]
    subprocess.run(npm_install_cmd, cwd=args.build_dir, check=True)
    subprocess.run(['npm', 'run', 'build'], cwd=args.build_dir, check=True)

    built_html = os.path.join(args.build_dir, 'build', 'index.html')
    inject_and_finalize_html(built_html, payload, args.output)


def main():
    parser = argparse.ArgumentParser(
        description='Generate single-file SvelteKit RTEMS release coverpage.'
    )
    parser.add_argument('--title', required=True, help='Site title')
    parser.add_argument('--release', required=True, help='Release string')
    parser.add_argument('--version', required=True, help='Version string')
    parser.add_argument('--revision', required=True, help='Revision string')
    parser.add_argument('--release-url', required=True, help='Release URL')
    parser.add_argument(
        '--release-notes', required=True, help='Release notes file/URL')
    parser.add_argument('--date', required=True, help='Release date')
    parser.add_argument(
        '--release-top', required=True, help='Release scripts top directory')
    parser.add_argument(
        '--site-template',
        required=True,
        help='Path to rtems-release-site template directory',
    )
    parser.add_argument(
        '--build-dir',
        required=True,
        help='Temporary build directory for SvelteKit',
    )
    parser.add_argument(
        '--readme-base', required=True, help='Path to README-base.md')
    parser.add_argument('--arch-bsp', required=True, help='Path to ARCH-BSP.md')
    parser.add_argument(
        '--output', required=True, help='Output index.html path')
    args = parser.parse_args()
    build_coverpage(args)


if __name__ == '__main__':
    main()
