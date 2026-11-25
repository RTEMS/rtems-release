<script>
  import { onMount } from 'svelte';
  import { Marked } from 'marked';
  import devReleaseData from '$lib/release-data.json';
  import defaultAssets from '$lib/rtems-assets.json';

  function loadReleaseData() {
    if (typeof document !== 'undefined') {
      const el = document.getElementById('rtems-release-data');
      if (el && el.textContent) {
        try {
          const parsedJson = JSON.parse(el.textContent);
          if (parsedJson && parsedJson.title) {
            return parsedJson;
          }
        } catch (err) {
          console.error('Failed to parse #rtems-release-data JSON:', err);
        }
      }
    }
    return devReleaseData;
  }

  const releaseData = loadReleaseData();

  const FALLBACK_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 84" width="280" height="84">' +
    '<g transform="translate(8, 8)">' +
    '<circle cx="34" cy="34" r="30" fill="none" stroke="#0284c7" stroke-width="5"/>' +
    '<ellipse cx="34" cy="34" rx="28" ry="11" transform="rotate(-28 34 34)" fill="none" stroke="#0ea5e9" stroke-width="2.5"/>' +
    '<ellipse cx="34" cy="34" rx="28" ry="11" transform="rotate(28 34 34)" fill="none" stroke="#38bdf8" stroke-width="2.5"/>' +
    '<circle cx="34" cy="34" r="7" fill="#0f172a"/>' +
    '<circle cx="57" cy="21" r="3.5" fill="#0284c7"/>' +
    '<circle cx="11" cy="47" r="3.5" fill="#0284c7"/>' +
    '</g>' +
    '<text x="84" y="45" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif" font-size="34" font-weight="800" letter-spacing="2" fill="#0f172a">RTEMS</text>' +
    '<text x="85" y="65" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif" font-size="11.5" font-weight="600" letter-spacing="1.4" fill="#475569">REAL-TIME EXECUTIVE</text>' +
    '</svg>';

  const FALLBACK_LOGO = 'data:image/svg+xml;utf8,' + encodeURIComponent(FALLBACK_SVG);

  let logoSrc = $state(releaseData.logoUrl || defaultAssets.logoUrl || FALLBACK_LOGO);
  const faviconHref = releaseData.faviconUrl || defaultAssets.faviconUrl || FALLBACK_LOGO;

  let mounted = $state(false);
  let showTopBtn = $state(false);
  let searchQuery = $state('');
  let openState = $state({});

  const architectures = releaseData.architectures || [];
  const archSummary = releaseData.archSummary || {};
  const releaseNotesHtmlHref = releaseData.release
    ? `rtems-${releaseData.release}-release-notes`
    : 'rtems-release-notes';

  onMount(() => {
    mounted = true;
    const link = document.getElementById('rtems-favicon');
    if (link && faviconHref) {
      link.setAttribute('href', faviconHref);
    }

    const onScroll = () => {
      showTopBtn = window.scrollY > 320;
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  });

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function handleLogoError() {
    if (logoSrc !== FALLBACK_LOGO) {
      logoSrc = FALLBACK_LOGO;
    }
  }

  function escapeAttr(val) {
    return String(val || '')
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  const cleanMarkdown = $derived.by(() => {
    let md = releaseData.markdown || '';
    md = md.replace(/\n?##\s+Architectures and BSPs[\s\S]*$/i, '');
    md = md.replace(
      /^\s*(?:---+\s*\n+)?\*\*Home:\*\*[\s\S]*?\*\*Date:\*\*[^\n]*\n+(?:---+\s*\n+)?/i,
      ''
    );
    return md.trim();
  });

  const parsed = $derived.by(() => {
    const headings = [];
    const marked = new Marked({
      gfm: true,
      breaks: false,
      renderer: {
        heading({ tokens, depth }) {
          const text = this.parser.parseInline(tokens);
          const plain = text.replace(/<[^>]+>/g, '');
          const id = plain
            .toLowerCase()
            .trim()
            .replace(/[^\w\s-]/g, '')
            .replace(/\s+/g, '-');

          if (depth >= 2 && depth <= 3) {
            headings.push({ depth: depth, text: plain, id: id });
          }
          return '<h' + depth + ' id="' + escapeAttr(id) + '">' + text + '</h' + depth + '>\n';
        },
        link({ href, title, tokens }) {
          const text = this.parser.parseInline(tokens);
          const safeHref = (href || '').trim();
          const titleAttr = title ? ' title="' + escapeAttr(title) + '"' : '';

          if (/^file:/i.test(safeHref)) {
            return '<code>' + text + '</code>';
          }

          if (safeHref.startsWith('#')) {
            return '<a href="' + escapeAttr(safeHref) + '"' + titleAttr + ' class="doc-link">' + text + '</a>';
          }
          if (/^https?:\/\//i.test(safeHref)) {
            return (
              '<a href="' +
              escapeAttr(safeHref) +
              '"' +
              titleAttr +
              ' target="_blank" rel="noopener noreferrer" class="ext-link">' +
              text +
              '</a>'
            );
          }
          return (
            '<a href="' +
            escapeAttr(safeHref) +
            '"' +
            titleAttr +
            ' data-sveltekit-reload class="doc-link">' +
            text +
            '</a>'
          );
        },
        table(token) {
          let headerHtml = '';
          if (token.header && token.header.length > 0) {
            const cells = token.header
              .map((cell) => {
                const align = cell.align ? ' style="text-align:' + escapeAttr(cell.align) + '"' : '';
                return '<th' + align + '>' + this.parser.parseInline(cell.tokens) + '</th>';
              })
              .join('');
            headerHtml = '<thead><tr>' + cells + '</tr></thead>';
          }

          const bodyRows = token.rows
            .map((row) => {
              const cells = row
                .map((cell) => {
                  const align = cell.align ? ' style="text-align:' + escapeAttr(cell.align) + '"' : '';
                  return '<td' + align + '>' + this.parser.parseInline(cell.tokens) + '</td>';
                })
                .join('');
              return '<tr>' + cells + '</tr>';
            })
            .join('');

          return (
            '<div class="table-scroll"><table class="data-table">' +
            headerHtml +
            '<tbody>' +
            bodyRows +
            '</tbody></table></div>\n'
          );
        }
      }
    });

    const html = marked.parse(cleanMarkdown);
    if (architectures.length > 0) {
      headings.push({
        depth: 2,
        text: 'Architectures and BSPs',
        id: 'architectures-and-bsps'
      });
    }
    return { html: html, headings: headings };
  });

  const filteredArchitectures = $derived.by(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) {
      return architectures.map((a) => ({
        arch: a.arch,
        meta: a.meta,
        rows: a.rows,
        filteredRows: a.rows,
        autoOpen: Boolean(openState[a.arch])
      }));
    }

    return architectures
      .map((a) => {
        const archMatch = a.arch.toLowerCase().includes(q);
        const matchingRows = archMatch
          ? a.rows
          : a.rows.filter(
              (r) =>
                r.bsp.toLowerCase().includes(q) || r.family.toLowerCase().includes(q)
            );
        return {
          arch: a.arch,
          meta: a.meta,
          rows: a.rows,
          filteredRows: matchingRows,
          autoOpen: true
        };
      })
      .filter((a) => a.filteredRows.length > 0);
  });

  function expandAll() {
    const next = {};
    for (const a of architectures) {
      next[a.arch] = true;
    }
    openState = next;
  }

  function collapseAll() {
    openState = {};
  }

  function handleToggle(arch, isOpen) {
    if (!searchQuery.trim()) {
      const next = Object.assign({}, openState);
      next[arch] = isOpen;
      openState = next;
    }
  }
</script>

<svelte:head>
  <title>{releaseData.title}</title>
</svelte:head>

<div class="page-wrapper">
  <header class="hero">
    <div class="hero-inner hero-flex">
      <a href="https://www.rtems.org/" class="logo-link" title="RTEMS Project Home">
        <img
          src={logoSrc}
          onerror={handleLogoError}
          alt="RTEMS Logo"
          class="rtems-logo"
        />
      </a>

      <div class="hero-content">
        <div class="badge-row">
          <span class="badge">RTEMS RELEASE {releaseData.release}</span>
          <span class="meta">Version {releaseData.version} · Revision {releaseData.revision}</span>
          <span class="meta">Built {releaseData.date}</span>
        </div>
        <h1>{releaseData.title}</h1>
        <div class="quick-links">
          <a href={releaseNotesHtmlHref} data-sveltekit-reload class="btn btn-primary">
            Release Notes
          </a>
          {#if releaseData.releaseNotes}
            <a
              href={releaseData.releaseNotes}
              target="_blank"
              rel="noopener noreferrer"
              class="btn btn-secondary"
            >
              Release Notes PDF ({releaseData.releaseNotes})
            </a>
          {/if}
          <a
            href="sources/"
            target="_blank"
            rel="noopener noreferrer"
            class="btn btn-secondary"
          >
            Source Tarballs
          </a>
          <a
            href="docs/html/"
            target="_blank"
            rel="noopener noreferrer"
            class="btn btn-secondary"
          >
            Online Docs
          </a>
          <a
            href="sha512sum.txt"
            target="_blank"
            rel="noopener noreferrer"
            class="btn btn-secondary"
          >
            SHA512 Checksums
          </a>
        </div>
      </div>
    </div>
  </header>

  <div class="layout">
    {#if parsed.headings.length > 0}
      <aside class="toc">
        <div class="toc-sticky">
          <h2>Contents</h2>
          <ul>
            {#each parsed.headings as h}
              <li class:sub={h.depth === 3}>
                <a href={'#' + h.id}>{h.text}</a>
              </li>
            {/each}
          </ul>

          <div class="filter-box">
            <label for="bsp-filter">Filter Architectures / BSPs</label>
            <input
              id="bsp-filter"
              type="search"
              bind:value={searchQuery}
              placeholder="e.g. aarch64, arm, zynq..."
            />
          </div>
        </div>
      </aside>
    {/if}

    <main class="markdown-body">
      {#if mounted}
        {@html parsed.html}
      {/if}

      {#if architectures.length > 0}
        <section class="arch-section">
          <h2 id="architectures-and-bsps">Architectures and BSPs</h2>

          {#if Object.keys(archSummary).length > 0}
            <div class="summary-pills">
              {#each Object.entries(archSummary) as [label, val]}
                <span class="summary-pill">
                  <strong>{label}:</strong> {val}
                </span>
              {/each}
            </div>
          {/if}

          <div class="arch-accordion-wrapper">
            <div class="arch-toolbar">
              <span class="arch-stats">
                Showing {filteredArchitectures.length} of {architectures.length} Architectures
              </span>
              <div class="arch-btn-group">
                <button type="button" class="arch-toggle-btn" onclick={expandAll}>
                  Expand All
                </button>
                <button type="button" class="arch-toggle-btn" onclick={collapseAll}>
                  Collapse All
                </button>
              </div>
            </div>

            {#each filteredArchitectures as archItem (archItem.arch)}
              <details
                class="arch-accordion"
                open={archItem.autoOpen}
                ontoggle={(e) => handleToggle(archItem.arch, e.currentTarget.open)}
              >
                <summary class="arch-summary">
                  <span class="arch-name">{archItem.arch}</span>
                  {#if archItem.meta}
                    <span class="arch-count">{archItem.meta}</span>
                  {/if}
                </summary>

                <div class="arch-body">
                  <div class="table-scroll">
                    <table class="data-table arch-table">
                      <thead>
                        <tr>
                          <th>BSP</th>
                          <th>BSP Family</th>
                        </tr>
                      </thead>
                      <tbody>
                        {#each archItem.filteredRows as row}
                          <tr>
                            <td><code>{row.bsp}</code></td>
                            <td>{row.family}</td>
                          </tr>
                        {/each}
                      </tbody>
                    </table>
                  </div>
                </div>
              </details>
            {/each}
          </div>
        </section>
      {/if}
    </main>
  </div>

  <footer class="footer">
    <p>
      RTEMS Tools Project (<a href="https://www.rtems.org/">https://www.rtems.org/</a>) · Release
      <code>{releaseData.release}</code> · {releaseData.date}
    </p>
  </footer>

  {#if showTopBtn}
    <button
      type="button"
      class="back-to-top"
      onclick={scrollToTop}
      title="Back to top"
      aria-label="Back to top"
    >
      ↑ Top
    </button>
  {/if}
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
      sans-serif;
    color: #1e293b;
    background: #f8fafc;
    line-height: 1.6;
  }

  .hero {
    background: #0f172a;
    color: #f8fafc;
    border-bottom: 4px solid #0284c7;
    padding: 2.5rem 1.5rem;
  }

  .hero-inner,
  .layout,
  .footer {
    max-width: 1240px;
    margin: 0 auto;
  }

  .hero-flex {
    display: flex;
    align-items: center;
    gap: 1.75rem;
  }

  .logo-link {
    display: flex;
    align-items: center;
    justify-content: center;
    background: #ffffff;
    padding: 0.55rem 0.85rem;
    border-radius: 8px;
    flex-shrink: 0;
    text-decoration: none;
  }

  .rtems-logo {
    display: block;
    height: 60px;
    width: auto;
    max-width: 240px;
    object-fit: contain;
  }

  .hero-content {
    min-width: 0;
    flex: 1;
  }

  @media (max-width: 640px) {
    .hero-flex {
      flex-direction: column;
      align-items: flex-start;
    }
  }

  .badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: center;
    margin-bottom: 0.75rem;
    font-size: 0.85rem;
  }

  .badge {
    background: #0284c7;
    color: #fff;
    font-weight: 700;
    padding: 0.2rem 0.65rem;
    border-radius: 4px;
    letter-spacing: 0.04em;
  }

  .meta {
    color: #94a3b8;
  }

  h1 {
    margin: 0 0 1.25rem;
    font-size: 1.95rem;
    font-weight: 700;
    line-height: 1.25;
  }

  .quick-links {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
  }

  .btn {
    display: inline-block;
    padding: 0.45rem 0.9rem;
    border-radius: 6px;
    text-decoration: none;
    font-size: 0.875rem;
    font-weight: 600;
    transition: background-color 0.15s ease;
  }

  .btn-primary {
    background: #0284c7;
    color: #ffffff;
  }

  .btn-primary:hover {
    background: #0369a1;
  }

  .btn-secondary {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
  }

  .btn-secondary:hover {
    background: #334155;
  }

  .layout {
    display: grid;
    grid-template-columns: 250px 1fr;
    gap: 2rem;
    padding: 2rem 1.5rem;
  }

  @media (max-width: 900px) {
    .layout {
      grid-template-columns: 1fr;
    }
  }

  .toc-sticky {
    position: sticky;
    top: 1.5rem;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1.1rem;
  }

  .toc h2 {
    margin: 0 0 0.75rem;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748b;
  }

  .toc ul {
    list-style: none;
    padding: 0;
    margin: 0 0 1.25rem;
  }

  .toc li {
    margin-bottom: 0.4rem;
    font-size: 0.9rem;
  }

  .toc li.sub {
    padding-left: 0.9rem;
    font-size: 0.84rem;
  }

  .toc a {
    color: #334155;
    text-decoration: none;
  }

  .toc a:hover {
    color: #0284c7;
  }

  .filter-box {
    border-top: 1px solid #e2e8f0;
    padding-top: 0.9rem;
  }

  .filter-box label {
    display: block;
    font-size: 0.78rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 0.35rem;
  }

  .filter-box input {
    width: 100%;
    box-sizing: border-box;
    padding: 0.4rem 0.6rem;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    font-size: 0.85rem;
  }

  .markdown-body {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 2rem 2.25rem;
    min-width: 0;
  }

  .markdown-body :global(h2),
  .markdown-body h2 {
    margin-top: 2.25rem;
    margin-bottom: 1rem;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid #e2e8f0;
    color: #0f172a;
    font-size: 1.4rem;
  }

  .markdown-body :global(h2:first-child) {
    margin-top: 0;
  }

  .markdown-body :global(h3) {
    margin-top: 1.75rem;
    margin-bottom: 0.75rem;
    color: #1e293b;
    font-size: 1.12rem;
  }

  .markdown-body :global(a.doc-link),
  .markdown-body :global(a.ext-link) {
    color: #0369a1;
    text-decoration: none;
    border-bottom: 1px solid #bae6fd;
    font-weight: 500;
    transition: color 0.15s ease, border-color 0.15s ease;
    word-break: break-word;
  }

  .markdown-body :global(a.doc-link:hover),
  .markdown-body :global(a.ext-link:hover) {
    color: #0c4a6e;
    border-bottom-color: #0284c7;
  }

  .markdown-body :global(a.ext-link::after) {
    content: ' ↗';
    font-size: 0.78em;
    opacity: 0.75;
  }

  .markdown-body :global(pre) {
    background: #0f172a;
    color: #e2e8f0;
    padding: 1rem 1.15rem;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 0.85rem;
    line-height: 1.5;
  }

  .markdown-body :global(code),
  .markdown-body code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.87em;
  }

  .markdown-body :global(p code),
  .markdown-body :global(td code) {
    background: #f1f5f9;
    padding: 0.12rem 0.35rem;
    border-radius: 4px;
    color: #0f172a;
  }

  .markdown-body :global(.table-scroll),
  .table-scroll {
    width: 100%;
    overflow-x: auto;
    margin: 1rem 0 1.5rem;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
  }

  .arch-body .table-scroll {
    margin: 0;
  }

  .markdown-body :global(.data-table),
  .data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 0;
    font-size: 0.89rem;
  }

  .markdown-body :global(.data-table th),
  .markdown-body :global(.data-table td),
  .data-table th,
  .data-table td {
    padding: 0.6rem 0.95rem;
    text-align: left;
    vertical-align: middle;
    line-height: 1.45;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
  }

  .markdown-body :global(.data-table th:last-child),
  .markdown-body :global(.data-table td:last-child),
  .data-table th:last-child,
  .data-table td:last-child {
    border-right: none;
  }

  .markdown-body :global(.data-table tbody tr:last-child td),
  .data-table tbody tr:last-child td {
    border-bottom: none;
  }

  .markdown-body :global(.data-table tbody tr:nth-child(even)),
  .data-table tbody tr:nth-child(even) {
    background: #f8fafc;
  }

  .markdown-body :global(.data-table tbody tr:hover),
  .data-table tbody tr:hover {
    background: #f0f9ff;
  }

  .markdown-body :global(.data-table th),
  .data-table th {
    background: #f1f5f9;
    font-weight: 600;
    color: #1e293b;
    border-bottom: 1px solid #cbd5e1;
    white-space: nowrap;
  }

  .summary-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    margin: 1rem 0;
  }

  .summary-pill {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.35rem 0.75rem;
    font-size: 0.88rem;
    color: #1e293b;
  }

  .arch-accordion-wrapper {
    margin: 1rem 0;
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
  }

  .arch-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 0.35rem;
    padding: 0.5rem 0.75rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
  }

  .arch-stats {
    font-size: 0.84rem;
    font-weight: 600;
    color: #475569;
  }

  .arch-btn-group {
    display: flex;
    gap: 0.5rem;
  }

  .arch-toggle-btn {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 0.3rem 0.65rem;
    font-size: 0.8rem;
    font-weight: 600;
    color: #334155;
    cursor: pointer;
  }

  .arch-toggle-btn:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
  }

  .arch-accordion {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    background: #ffffff;
    overflow: hidden;
  }

  .arch-summary {
    list-style: none;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.7rem 1rem;
    background: #f8fafc;
    cursor: pointer;
    user-select: none;
    font-weight: 600;
    color: #0f172a;
  }

  .arch-summary::-webkit-details-marker {
    display: none;
  }

  .arch-summary::before {
    content: '▶';
    font-size: 0.72rem;
    color: #0284c7;
    transition: transform 0.15s ease;
    margin-right: 0.6rem;
  }

  .arch-accordion[open] > .arch-summary::before {
    transform: rotate(90deg);
  }

  .arch-accordion[open] > .arch-summary {
    border-bottom: 1px solid #e2e8f0;
    background: #f1f5f9;
  }

  .arch-name {
    flex: 1;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.95rem;
  }

  .arch-count {
    font-size: 0.8rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-weight: 600;
    color: #0369a1;
    background: #e0f2fe;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    white-space: nowrap;
  }

  .arch-body {
    padding: 0.75rem 1rem;
    background: #ffffff;
  }

  .footer {
    padding: 1.5rem;
    text-align: center;
    font-size: 0.85rem;
    color: #64748b;
  }

  .footer a {
    color: #0369a1;
    text-decoration: none;
  }

  .back-to-top {
    position: fixed;
    right: 1.5rem;
    bottom: 1.5rem;
    z-index: 50;
    background: #0284c7;
    color: #ffffff;
    border: 1px solid #0369a1;
    border-radius: 999px;
    padding: 0.55rem 1rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2);
    transition: background-color 0.15s ease, transform 0.15s ease;
  }

  .back-to-top:hover {
    background: #0369a1;
    transform: translateY(-2px);
  }
</style>
