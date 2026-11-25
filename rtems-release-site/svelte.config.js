import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: undefined,
      precompress: false,
      strict: true
    }),
    paths: {
      relative: true
    },
    output: {
      bundleStrategy: 'inline'
    },
    prerender: {
      handleHttpError: 'warn'
    }
  }
};

export default config;
