import path from 'node:path';

const REPO = 'https://github.com/CMCC-TAO/open-rail';
const BRANCH = 'main';

/**
 * Rewrite cross-references in the docs into links that actually resolve on the
 * published site.
 *
 * Why this is needed: the docs live in `docs/` at the repository root, while the
 * Astro project root is `site/`. Astro only resolves relative `.md` links for
 * files that sit inside its own project, so without this plugin every
 * cross-reference in the docs is emitted verbatim — `href="guides/x.md"`,
 * `href="../README.md"` — and 404s once deployed (there are no `.md` files in
 * `dist/`, and root-relative routes are not prefixed with `base`).
 *
 * Two cases are handled, both limited to `.md` / `.mdx` targets so that image
 * references such as `../data/media/x.png` are left alone:
 *
 *   - a file inside `docs/`  -> the matching site route, with `base` prefixed
 *   - a file outside `docs/` -> the corresponding file on GitHub
 *
 * Anything with a scheme (`https:`, `mailto:`, ...), a protocol-relative URL, or
 * a pure in-page hash is passed through untouched.
 */
export default function remarkDocsLinks({ docsRoot, base }) {
  const repoRoot = path.resolve(docsRoot, '..');
  const prefix = base.endsWith('/') ? base.slice(0, -1) : base;

  return (tree, file) => {
    const source = file.history?.[0] ?? file.path;
    if (!source) return;
    const sourceDir = path.dirname(path.resolve(source));

    const toUrl = (rawUrl) => {
      const [pathname, ...rest] = rawUrl.split(/(?=[#?])/);
      const suffix = rest.join('');
      if (!/\.mdx?$/.test(pathname)) return null;
      if (/^[a-z][a-z0-9+.-]*:/i.test(pathname) || pathname.startsWith('//')) return null;

      const resolved = path.resolve(sourceDir, pathname);

      if (resolved === docsRoot || resolved.startsWith(docsRoot + path.sep)) {
        const rel = path.relative(docsRoot, resolved).split(path.sep).join('/');
        let route = `/${rel.replace(/\.mdx?$/, '')}`.replace(/\/index$/, '/');
        if (!route.endsWith('/')) route += '/';
        return prefix + route + suffix;
      }

      if (resolved === repoRoot || resolved.startsWith(repoRoot + path.sep)) {
        const rel = path.relative(repoRoot, resolved).split(path.sep).join('/');
        return `${REPO}/blob/${BRANCH}/${rel}${suffix}`;
      }

      return null;
    };

    const visit = (node) => {
      if (node.type === 'link' && typeof node.url === 'string') {
        const url = toUrl(node.url);
        if (url) node.url = url;
      }
      if (Array.isArray(node.children)) node.children.forEach(visit);
    };

    visit(tree);
  };
}
