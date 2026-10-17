/* Optional verification only; normal builds do not depend on Playwright. */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const http = require('node:http');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

async function main() {
  const [artifactDirectory] = process.argv.slice(2);
  assert(artifactDirectory, 'Usage: node scripts/check_browser.cjs /scratch/screenshots');
  const root = path.resolve('out');
  assert((await fs.stat(root)).isDirectory(), 'Build out/ before browser verification');
  const library = JSON.parse(await fs.readFile(path.join(root, 'data/library.json'), 'utf8'));
  await fs.mkdir(artifactDirectory, { recursive: true });
  const server = http.createServer(async (request, response) => {
    if (request.method !== 'GET') { response.writeHead(405).end(); return; }
    let pathname = new URL(request.url, 'http://localhost').pathname;
    if (pathname.startsWith('/peptide-wiki/')) pathname = pathname.slice('/peptide-wiki'.length);
    if (pathname === '/') pathname = '/index.html';
    const file = path.resolve(root, '.' + pathname);
    if (!file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
    try {
      const data = await fs.readFile(file);
      const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
        '.json': 'application/json', '.xml': 'application/xml', '.txt': 'text/plain' };
      response.setHeader('Content-Type', (types[path.extname(file)] || 'application/octet-stream') + '; charset=utf-8');
      response.end(data);
    } catch (error) {
      if (error.code === 'ENOENT' || error.code === 'EISDIR') response.writeHead(404).end();
      else { console.error(error); response.writeHead(500).end(); }
    }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  let browser;
  const results = [], errors = [];
  async function capture(page, name) {
    await page.screenshot({ path: path.join(artifactDirectory, name + '.png') });
  }
  async function noOverflow(page) {
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      'Unexpected horizontal page overflow: ' + page.url());
  }
  try {
    browser = await chromium.launch();
    for (const width of [320, 375, 714, 768, 860, 861, 1024, 1440]) {
      for (const colorScheme of ['light', 'dark']) {
        const context = await browser.newContext({ viewport: { width, height: 960 }, colorScheme });
        await context.route('**/*', route => new URL(route.request().url()).origin === origin
          ? route.continue() : route.abort());
        const page = await context.newPage();
        page.on('pageerror', error => errors.push(error.message));
        await page.goto(origin + '/peptide-wiki/index.html');
        const menu = page.locator('#navToggle'), nav = page.locator('#siteNav');
        if (width <= 860) {
          await menu.click();
          const buttonBox = await menu.boundingBox(), navBox = await nav.boundingBox();
          assert(navBox.y >= buttonBox.y + buttonBox.height, 'Expanded menu must start below the brand/toggle row at ' + width);
          assert(navBox.width >= width - 70, 'Expanded menu must span the content width at ' + width);
          if (width === 375 || width === 714) await capture(page, 'menu-' + width + '-' + colorScheme);
          await page.keyboard.press('Escape');
          assert.equal(await menu.getAttribute('aria-expanded'), 'false');
          assert.equal(await menu.evaluate(element => element === document.activeElement), true);
          assert.equal(await nav.isVisible(), false);
          await menu.click();
          await page.locator('#siteNav button').focus();
          await page.keyboard.press('Tab');
          assert.equal(await nav.isVisible(), false, 'Tabbing out should close the disclosure');
          await menu.click();
          await page.evaluate(() => document.querySelector('.hero').click());
          assert.equal(await nav.isVisible(), false, 'Outside click should close the disclosure');
          await menu.click();
          await page.setViewportSize({ width: 1024, height: 960 });
          await page.waitForFunction(() => document.querySelector('#navToggle').getAttribute('aria-expanded') === 'false');
          assert.equal(await menu.getAttribute('aria-expanded'), 'false');
          await page.setViewportSize({ width, height: 320 });
          assert.equal(await nav.isVisible(), false, 'Returning to mobile must not restore a stale open state');
          await menu.click();
          const bounds = await nav.boundingBox();
          assert(bounds.y + bounds.height <= 320, 'Expanded menu must fit a short viewport');
          await page.locator('#siteNav button').scrollIntoViewIfNeeded();
          assert(await nav.evaluate(element => element.scrollTop > 0), 'A short menu must scroll internally');
        } else {
          assert.equal(await menu.isVisible(), false);
          assert.equal(await nav.isVisible(), true);
        }
        await context.close();
      }
    }
    for (const width of [375, 714]) {
      const context = await browser.newContext({ viewport: { width, height: 960 }, javaScriptEnabled: false });
      await context.route('**/*', route => new URL(route.request().url()).origin === origin
        ? route.continue() : route.abort());
      const page = await context.newPage();
      await page.goto(origin + '/peptide-wiki/index.html');
      assert(await page.locator('#siteNav').isVisible(), 'Navigation must remain available without JavaScript');
      assert.equal(await page.locator('#navToggle').isVisible(), false, 'Do not show a non-working disclosure button');
      await context.close();
    }
    for (const width of [375, 768, 1440]) {
      for (const colorScheme of ['light', 'dark']) {
        const context = await browser.newContext({ viewport: { width, height: 960 }, colorScheme });
        await context.route('**/*', route => new URL(route.request().url()).origin === origin
          ? route.continue() : route.abort());
        const page = await context.newPage();
        page.on('pageerror', error => errors.push(error.message));
        for (const prefix of ['', '/peptide-wiki']) {
          const url = suffix => origin + prefix + suffix;
          const suffix = width + '-' + colorScheme + (prefix ? '-pages' : '-root');
          await page.goto(url('/index.html'));
          assert.equal(await page.title(), 'Biohacker Wiki');
          assert.equal(await page.evaluate(() => matchMedia('(prefers-color-scheme: dark)').matches), colorScheme === 'dark');
          await noOverflow(page);
          if (prefix) await capture(page, 'home-' + suffix);
          if (width < 861) {
            const menu = page.getByRole('button', { name: 'Menu', exact: true });
            await menu.focus();
            await page.keyboard.press('Enter');
            assert.equal(await menu.getAttribute('aria-expanded'), 'true');
            await page.keyboard.press('Tab');
            assert.equal(await page.evaluate(() => document.activeElement.textContent), 'Home');
            if (width === 375 && colorScheme === 'light' && prefix) await capture(page, 'mobile-menu');
            await menu.click();
          }
          assert.equal(await page.locator('.cat-card').count(), 8);
          for (const [slug, category] of Object.entries(library.categories)) {
            const card = page.locator('[data-category="' + slug + '"]');
            assert.equal(await card.locator('.card-count').innerText(), category.members.length + ' entries');
            const expected = {};
            for (const key of category.members) {
              const kind = library.entries[key].kind;
              expected[kind] = (expected[kind] || 0) + 1;
            }
            const actual = await card.locator('.category-counts > div').evaluateAll(rows =>
              Object.fromEntries(rows.map(row => [row.dataset.kind, Number(row.querySelector('dd').textContent)])));
            assert.deepEqual(actual, expected);
          }
          if (prefix && width !== 768) {
            await page.locator('[data-category="longevity"]').scrollIntoViewIfNeeded();
            await capture(page, 'category-cards-' + width + '-' + colorScheme);
          }
          await page.locator('[data-category="longevity"] .card-link').focus();
          await page.keyboard.press('Enter');
          await page.waitForURL('**/categories/longevity.html');
          const longevity = library.categories.longevity.members.map(key => library.entries[key]);
          assert.equal(await page.locator('section[id^="type-"]').count(), 8);
          for (const kind of new Set(longevity.map(entry => entry.kind))) {
            const actual = await page.locator('#type-' + kind + ' .card-grid > li > a').evaluateAll(links =>
              links.map(link => new URL(link.href).pathname));
            assert.deepEqual(actual, longevity.filter(entry => entry.kind === kind).map(entry => prefix + entry.path));
          }
          await noOverflow(page);
          if (prefix && width !== 768) await capture(page, 'category-longevity-' + width + '-' + colorScheme);
          await page.locator('a[href="#type-supplement"]').click();
          assert.equal(new URL(page.url()).hash, '#type-supplement');
          const heading = await page.locator('#heading-supplement').boundingBox();
          const header = await page.locator('.site-topbar').boundingBox();
          assert(heading.y >= header.y + header.height && heading.y < 960,
            'Category type jump must leave its heading visible below the sticky header');
          await page.goto(url('/library/supplement-caffeine.html'));
          await page.getByRole('link', { name: 'Nootropics & cognitive', exact: true }).click();
          await page.waitForURL('**/categories/nootropics-cognitive.html');
          assert(await page.getByRole('link', { name: /^Caffeine\b/ }).isVisible());
          await page.goto(url('/index.html'));
          await page.getByRole('searchbox', { name: 'Search the full library', exact: true }).fill('caffeine');
          await page.getByRole('searchbox', { name: 'Search the full library', exact: true }).press('Enter');
          await page.waitForURL('**/directory.html?q=caffeine');
          assert(await page.getByRole('link', { name: 'Caffeine', exact: true }).isVisible());
          await page.locator('#kindFilter').selectOption('supplement');
          assert(await page.getByRole('link', { name: 'Caffeine', exact: true }).isVisible());
          await noOverflow(page);
          if (width === 375 && colorScheme === 'light' && prefix) await capture(page, 'directory-filter');
          await page.locator('#dirFilter').fill('not-a-library-entry-zzzz');
          assert(await page.locator('#noResults').isVisible());
          assert.equal(await page.locator('#resultCount').textContent(), '0 matching entries');
          if (width === 768 && colorScheme === 'dark' && prefix) await capture(page, 'directory-empty');
          await page.locator('#dirFilter').fill('');
          await page.locator('#kindFilter').selectOption('');
          assert.equal(await page.locator('#resultCount').textContent(), '245 matching entries');
          await page.locator('th[data-sort]').first().focus();
          await page.keyboard.press('Enter');
          assert.equal(await page.locator('th[data-sort]').first().getAttribute('aria-sort'), 'ascending');
          await page.locator('#dirFilter').fill('</script><img src=x onerror=alert(1)>');
          assert(await page.locator('#noResults').isVisible());
          assert.equal(await page.locator('img').count(), 0);
          for (const [route, key] of [
            ['/peptides/bpc-157.html', 'peptide:bpc-157'],
            ['/stacks/bpc-157-tb-500.html', 'stack:bpc-157-tb-500'],
            ['/library/supplement-caffeine.html', 'library:supplement-caffeine'],
          ]) {
            await page.goto(url(route));
            const button = page.locator('[data-fav-key="' + key + '"]');
            const wasSaved = await button.getAttribute('aria-pressed') === 'true';
            await button.click();
            if (wasSaved) await button.click();
            assert.equal(await button.getAttribute('aria-pressed'), 'true');
            await noOverflow(page);
          }
          await page.goto(url('/favorites.html'));
          const caffeine = page.locator('#favoritesRoot a').filter({ hasText: /^Caffeine$/ });
          assert.equal(await caffeine.getAttribute('href'), url('/library/supplement-caffeine.html'));
          assert.equal(await page.locator('#favoritesRoot a').count(), 3);
          if (width === 1440 && colorScheme === 'light' && prefix) await capture(page, 'favorites');
          await caffeine.click();
          await page.waitForURL(url('/library/supplement-caffeine.html'));
          await page.waitForLoadState('domcontentloaded');
          assert.equal(await page.locator('.fav-toggle').getAttribute('aria-pressed'), 'true');
          await page.locator('.fav-toggle').click();
          await page.goto(url('/favorites.html'));
          assert.equal(await page.locator('#favoritesRoot a').count(), 2);
          await page.goto(url('/peptides/bpc-157.html'));
          assert((await page.locator('.research-warning').innerText()).includes('Half-life estimates differ'));
          await page.locator('a[href="#research-records"]').click();
          assert.equal(new URL(page.url()).hash, '#research-records');
          assert.equal(await page.locator('#research-records').count(), 1);
          assert.equal(await page.locator('#research').count(), 1);
          assert.equal(await page.locator('#research-records h2').first().innerText(), 'Research records');
          await page.locator('#research-records').scrollIntoViewIfNeeded();
          await noOverflow(page);
          if (width === 1440 && colorScheme === 'light' && prefix) await capture(page, 'bpc-research');
          await page.goto(url('/library/medication-paracetamol.html'));
          const finding = page.locator('.research-finding');
          await finding.locator('summary').click();
          assert((await finding.innerText()).includes('2026-10-06'));
          assert((await finding.innerText()).includes('No suitable community description'));
          await noOverflow(page);
          if (width === 375 && colorScheme === 'dark' && prefix) await capture(page, 'bounded-empty-finding');
          await page.goto(url('/library/context-sleep.html'));
          assert(await page.locator('.research-account').count() > 0);
          await noOverflow(page);
          await page.goto(url('/library/hormone-dhea.html#research-records'));
          const limitation = page.locator('.research-warning').filter({ hasText: '100 mg' });
          assert.equal(await limitation.count(), 1);
          assert((await page.locator('.research-status').allTextContents()).some(text => text.includes('not a clinical verification')));
          const account = page.locator('.research-account').first();
          assert.equal(await account.getAttribute('open'), null, 'Unverified account must be collapsed initially');
          await limitation.scrollIntoViewIfNeeded();
          if (prefix && ((width === 375 && colorScheme === 'light') || (width === 1440 && colorScheme === 'dark'))) {
            await capture(page, 'dhea-limitation-' + width + '-' + colorScheme);
          }
          await account.locator('summary').click();
          assert.notEqual(await account.getAttribute('open'), null);
          assert((await account.innerText()).includes('Unverified imported account'));
          assert.equal(await account.locator('blockquote').count(), 0);
          await noOverflow(page);
          if (prefix && ((width === 375 && colorScheme === 'dark') || (width === 1440 && colorScheme === 'light'))) {
            await capture(page, 'dhea-account-' + width + '-' + colorScheme);
          }
          await page.goto(url('/calculator.html'));
          assert.equal(await page.locator('#calcMg').inputValue(), '5');
          assert.equal(await page.locator('#calcWater').inputValue(), '2');
          assert.equal(await page.locator('#calcDose').inputValue(), '250');
          assert((await page.locator('#calcDoseText').innerText()).includes('0.1'));
          if (width === 768 && colorScheme === 'light' && prefix) await capture(page, 'calculator-unchanged');
          await page.locator('#calcWater').fill('0');
          assert.equal(await page.locator('#calcConcText').innerText(), 'Enter a vial amount and water volume above.');
          assert.equal(await page.locator('#calcDoseText').innerText(), '—');
          await noOverflow(page);
          await page.goto(url('/about.html'));
          assert((await page.locator('body').innerText()).includes('Publication suitability'));
          await noOverflow(page);
          results.push({ width, colorScheme, prefix: prefix || '/', passed: true });
        }
        await context.clearCookies();
        await context.addCookies([{ name: 'pw_favorites', value: '%7Bbroken', url: origin }]);
        await page.goto(origin + '/peptide-wiki/favorites.html');
        assert(await page.locator('#favoriteError').isVisible());
        if (width === 375 && colorScheme === 'light') await capture(page, 'malformed-favorites');
        await context.clearCookies();
        await page.goto(origin + '/peptide-wiki/library/supplement-caffeine.html');
        await page.evaluate(() => Object.defineProperty(document, 'cookie', {
          get: () => '', set: () => { throw new Error('Blocked at browser cookie boundary'); },
        }));
        await page.locator('.fav-toggle').click();
        assert((await page.locator('#favoriteError').innerText()).includes('could not be saved'));
        assert.equal(await page.locator('.fav-toggle').getAttribute('aria-pressed'), 'false');
        await context.close();
      }
    }
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(pathToFileURL(path.resolve('out/index.html')).href);
    assert(await page.locator('h1').isVisible());
    await page.getByRole('link', { name: 'Peptides', exact: true }).click();
    assert(await page.locator('.research-index').isVisible());
    await context.close();
    assert.deepEqual(errors, [], 'Uncaught browser errors');
    await fs.writeFile(path.join(artifactDirectory, 'results.json'), JSON.stringify({
      browser: browser.version(), results, uncaughtErrors: errors, fileLinks: 'passed',
      cookieFailure: 'explicit error; no success state', externalRequests: 'blocked',
      menu: '16 breakpoint/theme cases plus 2 no-JavaScript cases passed',
      publication: 'Visible limitations, collapsed unverified accounts and accessible disclosure passed',
    }, null, 2) + '\n');
    console.log('Passed 18 menu cases, 12 root/subpath × viewport/theme flows, file links and cookie-failure checks.');
    console.log('Screenshots and results: ' + path.resolve(artifactDirectory));
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
