import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

/**
 * Escapes HTML structural tags (`</script`, `<head`, `</head`, `<body`, `</body`, `<html`, `</html`)
 * inside inline `<script>` blocks so reverse-proxy HTML injectors (such as Apache mod_substitute
 * or nginx sub_filter injecting Matomo analytics) never match embedded SvelteKit error templates
 * or regexes inside JS strings.
 */
function sanitizeInlineScripts() {
  const tagPattern = /<(\/?(?:script|head|body|html))(?=\s|>|\/)/gi;
  return {
    name: 'sanitize-inline-scripts',
    transformIndexHtml(html) {
      return html.replace(
        /(<script(?![^>]*type=["']application\/json["'])[^>]*>)([\s\S]*?)(<\/script>)/gi,
        (_, open, body, close) =>
          open + body.replace(tagPattern, (_, tag) => '\x3C' + tag) + close
      );
    }
  };
}

export default defineConfig({
  plugins: [sveltekit(), sanitizeInlineScripts()]
});
