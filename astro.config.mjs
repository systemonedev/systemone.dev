// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightBlog from 'starlight-blog';

const SITE = 'https://systemone.dev';
const GITHUB = 'https://github.com/systemone-dev/systemone.dev';

export default defineConfig({
  site: SITE,
  integrations: [
    starlight({
      title: 'SystemOne.dev',
      description:
        'The community hub for decision-native AI: typed outputs, calibrated confidence, 70ms workflows, zero hallucinations.',
      logo: {
        light: './src/assets/logo-light.svg',
        dark: './src/assets/logo-dark.svg',
        replacesTitle: true,
      },
      favicon: '/favicon.svg',
      customCss: ['./src/styles/theme.css'],
      editLink: { baseUrl: `${GITHUB}/edit/main/` },
      lastUpdated: true,
      pagination: true,
      social: [
        { icon: 'github', label: 'GitHub', href: GITHUB },
        { icon: 'discord', label: 'Discord', href: 'https://discord.gg/systemone' },
        { icon: 'rss', label: 'RSS', href: `${SITE}/blog/rss.xml` },
      ],
      plugins: [
        starlightBlog({
          title: 'Blog',
          postCount: 10,
          recentPostCount: 5,
          authors: {
            maintainers: {
              name: 'SystemOne Maintainers',
              title: 'Community stewards',
              url: GITHUB,
            },
          },
        }),
      ],
      // Top-level nav maps 1:1 to the spec: Concepts | Cookbook | Projects | Blog | GitHub.
      // Starlight renders the matching sidebar tree automatically per section.
      sidebar: [
        {
          label: 'Start Here',
          items: [
            { label: 'Welcome', link: '/start/' },
            { label: 'Quickstart: your first decision', link: '/start/quickstart/' },
            { label: 'Is System 1 right for my problem?', link: '/start/when-to-use/' },
          ],
        },
        {
          label: 'Concepts',
          collapsed: false,
          items: [{ autogenerate: { directory: 'concepts' } }],
        },
        {
          label: 'Cookbook',
          collapsed: false,
          items: [{ autogenerate: { directory: 'cookbook' } }],
        },
        {
          label: 'Projects',
          collapsed: false,
          items: [{ autogenerate: { directory: 'projects' } }],
        },
        {
          label: 'Community',
          collapsed: true,
          items: [{ autogenerate: { directory: 'community' } }],
        },
      ],
      components: {
        // Adds the horizontal section nav described in the spec's Top Nav.
        SiteTitle: './src/components/SiteTitle.astro',
      },
      head: [
        {
          tag: 'meta',
          attrs: { property: 'og:image', content: `${SITE}/og.png` },
        },
        {
          tag: 'meta',
          attrs: { name: 'twitter:card', content: 'summary_large_image' },
        },
      ],
    }),
  ],
});
