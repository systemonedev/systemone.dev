#!/usr/bin/env node
/**
 * Verifies every internal link and heading anchor in the built site resolves.
 *
 * Cross-links between Concepts, Cookbook, and Projects carry a lot of this site's
 * value, and a renamed heading breaks them silently. This runs in CI against `dist/`.
 *
 *   node scripts/linkcheck.mjs [distDir]
 */
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const DIST = process.argv[2] ?? 'dist';

if (!existsSync(DIST)) {
  console.error(`linkcheck: "${DIST}" not found — run \`npm run build\` first.`);
  process.exit(1);
}

function walk(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (entry.endsWith('.html')) out.push(p);
  }
  return out;
}

const toRoute = (file) =>
  '/' +
  relative(DIST, file)
    .replaceAll('\\', '/')
    .replace(/index\.html$/, '')
    .replace(/\.html$/, '/');

const files = walk(DIST);

// route -> set of element ids on that page
const anchors = new Map(
  files.map((f) => [
    toRoute(f),
    new Set([...readFileSync(f, 'utf8').matchAll(/\sid="([^"]+)"/g)].map((m) => m[1])),
  ]),
);

let problems = 0;

for (const file of files) {
  const from = toRoute(file);
  const html = readFileSync(file, 'utf8');

  for (const [, rawPath, hash] of html.matchAll(/href="(\/[^"#]*)(#[^"]*)?"/g)) {
    // Build assets and the search index are not routes.
    if (rawPath.startsWith('/_astro') || rawPath.startsWith('/pagefind')) continue;

    let path = rawPath;
    if (!path.endsWith('/')) {
      // A real file such as /favicon.svg, /blog/rss.xml, /sitemap-index.xml.
      if (existsSync(join(DIST, path))) continue;
      path += '/';
    }

    if (!anchors.has(path)) {
      console.error(`broken link    ${from} -> ${rawPath}${hash ?? ''}`);
      problems++;
      continue;
    }

    if (hash) {
      const id = decodeURIComponent(hash.slice(1));
      if (id && !anchors.get(path).has(id)) {
        console.error(`broken anchor  ${from} -> ${path}${hash}`);
        problems++;
      }
    }
  }
}

if (problems > 0) {
  console.error(`\nlinkcheck: ${problems} problem(s) across ${files.length} pages.`);
  process.exit(1);
}

console.log(`linkcheck: all internal links and anchors resolve across ${files.length} pages.`);
