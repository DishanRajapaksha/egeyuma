import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: undefined,
      precompress: false,
      strict: true
    }),
    paths: {
      base: process.env.BASE_PATH ?? ''
    },
    prerender: {
      handleHttpError: ({ path, referrer, message }) => {
        const ignoredLinkedAssets = [`${process.env.BASE_PATH ?? ''}/docs/`, `${process.env.BASE_PATH ?? ''}/results`];

        if (referrer === `${process.env.BASE_PATH ?? ''}/` && ignoredLinkedAssets.includes(path)) {
          return;
        }

        throw new Error(message);
      }
    }
  }
};

export default config;
