# Deploying systemone.dev

The site builds to static HTML: no server, no database, no secrets. Hosting is free and the site is
very hard to break.

It's deployed on **Cloudflare Workers** as static assets: free, works with GitHub organisation
repositories, and gives every pull request a preview build. `wrangler.jsonc` tells Cloudflare to serve
the built `dist/` folder; there's no Worker code. Alternatives are at the bottom.

---

## 1. Connect the repository

1. In the [Cloudflare dashboard](https://dash.cloudflare.com), go to **Workers & Pages → Create →
   Import a repository**.
2. Install the Cloudflare GitHub app on the **systemonedev** organisation, with access to
   `systemone.dev` only.
3. Pick `systemonedev/systemone.dev` and set:

   | Setting | Value |
   | :--- | :--- |
   | Project name | `systemone-dev` (must match `name` in `wrangler.jsonc`) |
   | Production branch | `main` |
   | Build command | `npm run build` |
   | Deploy command | `npx wrangler deploy` |
   | Environment variable | `NODE_VERSION` = `22` |

4. Save and deploy. You get a `*.workers.dev` URL straight away. Every push to `main` redeploys, and
   pull requests get a preview build reported on the PR.

To check the setup locally before pushing: `npm run build && npx wrangler deploy --dry-run`, or
`npx wrangler dev` to serve the site exactly as Cloudflare will.

## 2. Point the domain at it

Cloudflare can only serve an apex domain (`systemone.dev`, without `www`) when the domain's DNS
is on Cloudflare. That's free:

1. In the same Cloudflare account, go to **Websites → Add a domain**, enter
   `systemone.dev`, and choose the **Free** plan. Cloudflare imports your existing DNS records:
   check them, especially any email (MX) records.
2. Cloudflare shows two **nameservers**. At your registrar (where you bought systemone.dev), replace
   the domain's nameservers with those two. This usually takes minutes, occasionally up to a day.
3. Once Cloudflare says the domain is **Active**: **Workers & Pages → systemone-dev → Settings →
   Domains & Routes → Add → Custom domain**. Add `systemone.dev`, then `www.systemone.dev`.
   Cloudflare creates the DNS records and the TLS certificates itself.
4. Send `www` to the apex: **Rules → Redirect Rules → Create rule → "Redirect from WWW to root"**
   template.

`.dev` is on the HSTS preload list, so browsers require HTTPS. Cloudflare handles that, and
`public/_headers` sends a matching `Strict-Transport-Security` header.

## 3. After the first deploy

- **Check `site` in `astro.config.mjs`.** It's `https://systemone.dev`, and it generates canonical
  URLs, `sitemap-index.xml` and the blog's RSS feed. Wrong values here are invisible in the browser but
  wrong in every feed reader and search engine.
- **Submit the sitemap** (`https://systemone.dev/sitemap-index.xml`) to Google Search Console.
- **Confirm search works.** Starlight builds a [Pagefind](https://pagefind.app) index at build time,
  so it only works on the deployed site or with `npm run preview`, not `npm run dev`.
- **Check the social card.** Paste a page URL into a link preview (Slack, LinkedIn's Post Inspector):
  it should show `public/og.png`.

---

## What is in `public/_headers`

- **Immutable caching for `/_astro/*`.** Those filenames are content-hashed, so they're safe to cache
  for a year.
- **Security headers:** `nosniff`, `SAMEORIGIN`, a strict referrer policy, a locked-down permissions
  policy, and HSTS.

`wrangler.jsonc` sets `html_handling: auto-trailing-slash`, so `/concepts/` is served from
`concepts/index.html` and `/concepts` redirects to it (Astro's directory-style output), and
`not_found_handling: 404-page`, so unknown URLs get `404.html`.

## CI

`.github/workflows/ci.yml` runs on every push to `main` and every pull request:

1. `npm ci`
2. `npm run build`: `astro check` validates content frontmatter against the schema, then builds
3. `npm run linkcheck`: fails on any broken internal link or heading anchor

The link check matters more than it looks. The cross-links between Concepts, Cookbook and Projects are
much of this site's value, and renaming a heading silently breaks every deep link to it.

Cloudflare builds independently of GitHub Actions, so a green CI run is a signal, not a gate. To make
it a gate, protect `main` and require the `build` check.

---

## Alternatives

The build output is plain static files, so any static host works.

### Cloudflare Pages

Also works: create a **Pages** project instead (Astro preset, output `dist`, `NODE_VERSION=22`). It
reads `public/_headers` too and ignores `wrangler.jsonc`.

### GitHub Pages

Free for public repositories, with no other account. Use
[`withastro/action`](https://github.com/withastro/action), add `public/CNAME` containing
`systemone.dev`, and point the domain at GitHub's Pages IPs. GitHub Pages ignores `_headers`, and
there are no per-PR previews.

### Netlify

```toml
# netlify.toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "22"
```

Netlify also reads `public/_headers`.

### Vercel

Works, but connecting a GitHub organisation repository needs a paid plan. Recreate the headers in a
`vercel.json` (see this file's git history).

### Self-hosted

```bash
npm ci && npm run build
# serve dist/ with nginx, Caddy, or any static file server
```

Configure the server to serve `dist/404.html` for unmatched routes and to treat `/path/` as
`/path/index.html`.
