# Deploying systemone.dev

The site builds to static HTML. There is no server, no database, and no environment variables —
which keeps hosting free or nearly free and makes the site very hard to break.

Vercel is the recommended target and the one `vercel.json` is written for. Alternatives are at
the bottom.

---

## 1. The repository

The site lives at `https://github.com/systemonedev/systemone.dev`. If you fork it to deploy
elsewhere, update the `GITHUB` constant at the top of `astro.config.mjs`: it drives every "Edit
page" link.

## 2. Import on Vercel

1. Go to [vercel.com/new](https://vercel.com/new) and import the repository.
2. Vercel detects Astro and reads `vercel.json`. The settings should already read:
   - **Framework preset:** Astro
   - **Build command:** `npm run build`
   - **Output directory:** `dist`
   - **Install command:** `npm ci`
3. No environment variables are needed.
4. Deploy.

You get a `*.vercel.app` URL immediately. Every push to `main` redeploys production; every pull
request gets its own preview URL.

### Or from the CLI

```bash
npm i -g vercel
vercel login
vercel          # preview deployment
vercel --prod   # production
```

## 3. Point the domain at it

In **Vercel → Project → Settings → Domains**, add both `systemone.dev` and `www.systemone.dev`.
Vercel will show the exact records to create at your registrar:

| Record | Name | Value |
| :--- | :--- | :--- |
| `A` | `@` | `76.76.21.21` |
| `CNAME` | `www` | `cname.vercel-dns.com` |

Verify the values Vercel shows you rather than copying these — they do change.

Set `systemone.dev` as the primary domain so `www` redirects to it. TLS is provisioned
automatically; DNS propagation is usually minutes.

:::note
`.dev` is on the HSTS preload list, so browsers require HTTPS. This is automatic with Vercel,
and `vercel.json` already sends a matching `Strict-Transport-Security` header.
:::

## 4. After the first deploy

- **Check `site` in `astro.config.mjs`.** It is set to `https://systemone.dev` and is what
  generates canonical URLs, `sitemap-index.xml`, and the blog RSS feed. If you deploy under a
  different domain, change it — wrong values here are invisible in the browser but wrong in
  every feed reader and search engine.
- **Submit the sitemap** at `https://systemone.dev/sitemap-index.xml` to Google Search Console.
- **Confirm search works.** Starlight builds a [Pagefind](https://pagefind.app) index at build
  time; it only works against the built site, so test it on the deployment or via
  `npm run preview`, not `npm run dev`.
- **Add an OG image.** `astro.config.mjs` references `/og.png`; drop a 1200×630 image at
  `public/og.png`. Until then social cards fall back to text.

---

## What is in `vercel.json`

- **`trailingSlash: true`** — matches Astro's directory-style output (`/concepts/`). Getting
  this wrong causes a redirect on every page load.
- **Immutable caching for `/_astro/*`** — those filenames are content-hashed, so they are safe
  to cache for a year.
- **Security headers** — `nosniff`, `SAMEORIGIN`, a strict referrer policy, a locked-down
  permissions policy, and HSTS.

## CI

`.github/workflows/ci.yml` runs on every push to `main` and every PR:

1. `npm ci`
2. `npm run build` — `astro check` validates content frontmatter against the schema, then builds
3. `npm run linkcheck` — fails on any broken internal link or heading anchor

The link check matters more than it looks. The cross-links between Concepts, Cookbook, and
Projects are much of this site's value, and renaming a heading silently breaks every deep link
to it.

Vercel builds independently of GitHub Actions, so a green CI run is a signal, not a gate. To
make it a real gate, enable branch protection on `main` requiring the `build` check.

---

## Alternatives to Vercel

The build output is plain static files, so any static host works. Only the config file differs.

### Netlify

```toml
# netlify.toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "22"
```

### Cloudflare Pages

- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `NODE_VERSION=22`

### GitHub Pages

Works, with two caveats: set `site` and `base` correctly in `astro.config.mjs` if the repo is
not served from the domain root, and use
[`withastro/action`](https://github.com/withastro/action) rather than a hand-rolled workflow.

### Self-hosted

```bash
npm ci && npm run build
# serve dist/ with nginx, Caddy, or any static file server
```

Configure the server to serve `dist/404.html` for unmatched routes and to treat
`/path/` as `/path/index.html`.
