import type { Config } from '@docusaurus/types';
import type { Options as ClassicPresetOptions } from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Egeyuma Docs',
  tagline: 'Documentation for Sinhala and Sri Lankan-context LLM evaluation tooling.',
  favicon: 'img/favicon.ico',

  url: 'https://dishanrajapaksha.github.io',
  baseUrl: '/egeyuma/',
  organizationName: 'DishanRajapaksha',
  projectName: 'egeyuma',

  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn'
    }
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en']
  },

  presets: [
    [
      'classic',
      {
        docs: false,
        blog: false,
        theme: {
          customCss: './src/css/custom.css'
        }
      } satisfies ClassicPresetOptions
    ]
  ],

  plugins: [
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'engine',
        path: '../engine/docs',
        routeBasePath: 'engine',
        sidebarPath: './engineSidebars.ts',
        editUrl: 'https://github.com/DishanRajapaksha/egeyuma/tree/main/engine/docs/'
      }
    ],
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'dashboard',
        path: '../dashboard/docs',
        routeBasePath: 'dashboard',
        sidebarPath: './dashboardSidebars.ts',
        editUrl: 'https://github.com/DishanRajapaksha/egeyuma/tree/main/dashboard/docs/'
      }
    ]
  ],

  themeConfig: {
    navbar: {
      title: 'Egeyuma',
      items: [
        { to: '/engine/', label: 'Engine', position: 'left' },
        { to: '/dashboard/', label: 'Dashboard', position: 'left' },
        {
          href: 'https://github.com/DishanRajapaksha/egeyuma',
          label: 'GitHub',
          position: 'right'
        }
      ]
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            { label: 'Engine', to: '/engine/' },
            { label: 'Dashboard', to: '/dashboard/' }
          ]
        },
        {
          title: 'Project',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/DishanRajapaksha/egeyuma'
            }
          ]
        }
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Egeyuma`
    },
    prism: {
      theme: require('prism-react-renderer').themes.github,
      darkTheme: require('prism-react-renderer').themes.dracula
    }
  }
};

export default config;
