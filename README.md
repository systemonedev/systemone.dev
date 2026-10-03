# systemone.dev

**The open community for System One decision models.** Live at **[systemone.dev](https://systemone.dev)**.

Learn to build with models that answer typed questions about your program's state with calibrated
probabilities, in milliseconds, without generating text. Every code sample runs against open models
([Kenning](https://huggingface.co/systemonedev/kenning-large-v0.4)) through the
[`systemone-client`](https://pypi.org/project/systemone-client/) package, and works unchanged with Clef
and Jev.

Part of [systemonedev](https://github.com/systemonedev), alongside
[SystemOne Builder](https://github.com/systemonedev/systemone-builder). Built with
[Astro](https://astro.build) + [Starlight](https://starlight.astro.build), deployed as a static site on
Cloudflare Workers.

## Quick start

Node **22.12 or newer** (`.nvmrc` pins 22).

```bash
npm ci               # install exactly what package-lock.json records
npm run dev          # http://localhost:4321
```

| Script | What it does |
| :--- | :--- |
| `npm run dev` | Dev server with hot reload |
| `npm run build` | `astro check` (content schema + types), then a production build to `dist/` |
| `npm run build:fast` | Build without the type-check |
| `npm run preview` | Serve the built `dist/` locally (needed to test search) |
| `npm run linkcheck` | Verify every internal link and heading anchor in `dist/` resolves |

CI runs `npm ci`, `npm run build` and `npm run linkcheck` on every pull request. If you change
dependencies, commit the updated `package-lock.json`: `npm ci` fails when it's out of sync.

## Structure

```text
src/
├── assets/                 Logo (light and dark)
├── components/
│   └── SiteTitle.astro     Header override: logo + top-level section nav
├── content.config.ts       Starlight docs collection + blog schema
├── content/docs/
│   ├── index.mdx           Splash homepage
│   ├── 404.md
│   ├── start/              Welcome, quickstart, when to use it, engines
│   ├── concepts/           Mental models: the "unlearning" section
│   ├── cookbook/           Integration patterns
│   ├── projects/           End-to-end builds
│   ├── community/          Overview, contributing, roadmap
│   └── blog/               Dated posts (starlight-blog)
└── styles/theme.css        Dark-first slate / desaturated-blue theme
public/
├── _headers                Cloudflare security and cache headers
├── og.png                  Social card (1200×630)
├── favicon.svg
└── robots.txt
scripts/linkcheck.mjs       Internal link and anchor checker
```

Navigation is configured in `astro.config.mjs`. Each section's sidebar is generated from its directory,
so adding a Markdown file is all it takes to add a page.

## Contributing

Every page has an **Edit page** link that opens it here on GitHub. For anything bigger, see the
[contributing guide](https://systemone.dev/community/contributing/) (source:
[`src/content/docs/community/contributing.md`](src/content/docs/community/contributing.md)). It covers
frontmatter, blog posts, and the writing standard pages are held to: code that runs, real outputs, and
limits stated next to claims.

Questions and ideas: [Discussions](https://github.com/systemonedev/systemone-builder/discussions).
Everyone taking part follows the [code of conduct](https://github.com/systemonedev/.github/blob/main/CODE_OF_CONDUCT.md).

## Deploying

See [DEPLOY.md](DEPLOY.md). Short version: import the repo in Cloudflare Workers (build `npm run build`,
deploy `npx wrangler deploy`, `NODE_VERSION=22`; `wrangler.jsonc` serves `dist/`), move the domain's DNS
to Cloudflare, and add `systemone.dev` as a custom domain.

## Licence

- **Content** (everything under `src/content/`): [CC BY 4.0](LICENSE-CONTENT)
- **Code** (everything else): [MIT](LICENSE)
