import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const DEFAULT_SHARED_URL =
  'https://1drv.ms/f/c/688565bd0cf9300c/IgA9Urm-Z-aoQLJaBEnLfJCqAdlJbMsxYpTwPJazxd8mQzk?e=zhoDbn';

const sharedUrl = process.argv[2] || DEFAULT_SHARED_URL;
const outputBase = path.resolve(process.argv[3] || 'onedrive-manifest');
const headless = process.argv.includes('--headless');
const folderArgument = process.argv.find((argument) => argument.startsWith('--folder='));
const targetFolderName = folderArgument?.slice('--folder='.length) || 'Media';

const browser = await chromium.launch({
  channel: 'msedge',
  headless,
});

const context = await browser.newContext({
  locale: 'es-ES',
  acceptDownloads: false,
});

const page = await context.newPage();
page.setDefaultTimeout(30_000);

const manifest = [];
const visitedFolders = new Set();
let publicContext;

function buildPublicUrl(itemId) {
  const url = new URL('https://onedrive.live.com/');
  url.searchParams.set('redeem', publicContext.redeem);
  url.searchParams.set('id', itemId);
  url.searchParams.set('cid', publicContext.cid);
  return url.toString();
}

function csvEscape(value) {
  const text = value == null ? '' : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

async function waitForFolder() {
  await page.waitForURL(/onedrive\.live\.com\/.*[?&]id=/i, { timeout: 90_000 });
  await page.locator('[role="grid"]').waitFor({ state: 'visible', timeout: 90_000 });
}

async function readVisibleItems() {
  return page.locator('[data-drop-target-key]').evaluateAll((containers) => {
    const result = [];

    for (const container of containers) {
      const rawKey = container.getAttribute('data-drop-target-key') || '';
      const idMatch = rawKey.match(/([0-9a-f]{16}![a-z0-9_-]+)/i);
      if (!idMatch) continue;

      const row = container.querySelector('[role="row"]');
      const link = row?.querySelector('[role="link"], a, button[data-automationid="FieldRenderer-name"]');
      const checkbox = row?.querySelector('[role="checkbox"]');
      const name =
        link?.getAttribute('title')?.trim() ||
        link?.textContent?.trim() ||
        checkbox?.getAttribute('title')?.trim();

      if (!name) continue;

      const label = row?.getAttribute('aria-label') || '';
      const isFolder = /(?:^|,\s*)(Carpeta|Folder)(?:,|$)/i.test(label);
      const childCountMatch = label.match(/(?:contiene|contains)\s+(\d+)\s+(?:elementos|items)/i);

      result.push({
        name,
        id: idMatch[1],
        type: isFolder ? 'folder' : 'file',
        childCount: childCountMatch ? Number(childCountMatch[1]) : null,
        ariaLabel: label,
      });
    }

    return result;
  });
}

async function findScrollContainer() {
  return page.locator('[role="grid"]').evaluate((grid) => {
    let element = grid;
    while (element) {
      if (element.scrollHeight > element.clientHeight + 5) {
        return {
          found: true,
          scrollTop: element.scrollTop,
          scrollHeight: element.scrollHeight,
          clientHeight: element.clientHeight,
        };
      }
      element = element.parentElement;
    }
    return { found: false };
  });
}

async function setScrollTop(value) {
  await page.locator('[role="grid"]').evaluate((grid, nextTop) => {
    let element = grid;
    while (element) {
      if (element.scrollHeight > element.clientHeight + 5) {
        element.scrollTop = nextTop;
        element.dispatchEvent(new Event('scroll', { bubbles: true }));
        return;
      }
      element = element.parentElement;
    }
  }, value);
}

async function collectFolderItems() {
  const found = new Map();
  let unchangedRounds = 0;
  let previousSize = -1;

  await setScrollTop(0);
  await page.waitForTimeout(400);

  for (let round = 0; round < 200; round += 1) {
    for (const item of await readVisibleItems()) found.set(item.id, item);

    if (found.size === previousSize) unchangedRounds += 1;
    else unchangedRounds = 0;
    previousSize = found.size;

    const scroll = await findScrollContainer();
    if (!scroll.found || scroll.scrollTop + scroll.clientHeight >= scroll.scrollHeight - 3) {
      if (unchangedRounds >= 2 || !scroll.found) break;
    }

    const nextTop = Math.min(
      scroll.scrollTop + Math.max(250, Math.floor(scroll.clientHeight * 0.8)),
      scroll.scrollHeight,
    );
    await setScrollTop(nextTop);
    await page.waitForTimeout(350);
  }

  return [...found.values()];
}

async function visitFolder(folderId, relativePath) {
  if (visitedFolders.has(folderId)) return;
  visitedFolders.add(folderId);

  const folderUrl = buildPublicUrl(folderId);
  console.log(`Carpeta: ${relativePath || '/'}`);
  await page.goto(folderUrl, { waitUntil: 'domcontentloaded', timeout: 90_000 });
  await waitForFolder();
  await page.waitForTimeout(1_500);

  const items = await collectFolderItems();
  console.log(`  ${items.length} elemento(s)`);

  for (const item of items) {
    const itemPath = relativePath ? `${relativePath}/${item.name}` : item.name;
    manifest.push({
      path: itemPath,
      name: item.name,
      type: item.type,
      id: item.id,
      cid: publicContext.cid,
      parentId: folderId,
      childCount: item.childCount,
      publicUrl: buildPublicUrl(item.id),
    });
  }

  for (const item of items.filter((candidate) => candidate.type === 'folder')) {
    const itemPath = relativePath ? `${relativePath}/${item.name}` : item.name;
    await visitFolder(item.id, itemPath);
  }
}

try {
  console.log('Abriendo el enlace compartido en una sesion anonima...');
  await page.goto(sharedUrl, { waitUntil: 'domcontentloaded', timeout: 90_000 });
  await waitForFolder();
  await page.waitForTimeout(2_000);

  const redeemedUrl = new URL(page.url());
  const redeem = redeemedUrl.searchParams.get('redeem');
  const cid = redeemedUrl.searchParams.get('cid');
  const rootId = redeemedUrl.searchParams.get('id');

  if (!redeem || !cid || !rootId) {
    throw new Error(`OneDrive no expuso redeem, cid e id en la URL final: ${page.url()}`);
  }

  publicContext = { redeem, cid, rootId };
  console.log(`CID: ${cid}`);
  console.log(`Raiz: ${rootId}`);

  const rootItems = await collectFolderItems();
  const targetFolder = rootItems.find(
    (item) => item.type === 'folder' && item.name.localeCompare(targetFolderName, 'es', { sensitivity: 'accent' }) === 0,
  );
  if (!targetFolder) {
    const availableFolders = rootItems
      .filter((item) => item.type === 'folder')
      .map((item) => item.name)
      .join(', ');
    throw new Error(
      `No se encontro la carpeta '${targetFolderName}' en la raiz. Carpetas disponibles: ${availableFolders || '(ninguna)'}`,
    );
  }

  console.log(`Ambito: ${targetFolder.name} (${targetFolder.id})`);
  await visitFolder(targetFolder.id, '');

  manifest.sort((a, b) => a.path.localeCompare(b.path, 'es'));

  const jsonPath = `${outputBase}.json`;
  const csvPath = `${outputBase}.csv`;
  await fs.mkdir(path.dirname(jsonPath), { recursive: true });

  await fs.writeFile(
    jsonPath,
    `${JSON.stringify(
      {
        generatedAt: new Date().toISOString(),
        sharedUrl,
        redeemedUrl: redeemedUrl.toString(),
        cid,
        sharedRootId: rootId,
        scope: {
          name: targetFolder.name,
          id: targetFolder.id,
          publicUrl: buildPublicUrl(targetFolder.id),
        },
        count: manifest.length,
        items: manifest,
      },
      null,
      2,
    )}\n`,
    'utf8',
  );

  const columns = ['path', 'name', 'type', 'id', 'cid', 'parentId', 'childCount', 'publicUrl'];
  const csv = [
    columns.join(','),
    ...manifest.map((item) => columns.map((column) => csvEscape(item[column])).join(',')),
  ].join('\r\n');
  await fs.writeFile(csvPath, `\uFEFF${csv}\r\n`, 'utf8');

  console.log('');
  console.log(`Manifest JSON: ${jsonPath}`);
  console.log(`Manifest CSV:  ${csvPath}`);
  console.log(`Elementos:     ${manifest.length}`);
} catch (error) {
  const diagnosticPath = `${outputBase}-error.html`;
  await fs.mkdir(path.dirname(diagnosticPath), { recursive: true });
  try {
    await page.waitForLoadState('domcontentloaded', { timeout: 5_000 });
  } catch {
    // La pagina puede continuar navegando; conservamos siempre el error original.
  }
  try {
    const diagnosticHtml = await page.content();
    await fs.writeFile(diagnosticPath, diagnosticHtml, 'utf8');
  } catch {
    // No ocultar el error original si el navegador no permite leer el HTML.
  }
  console.error('');
  console.error(error?.stack || error);
  console.error(`HTML de diagnostico: ${diagnosticPath}`);
  process.exitCode = 1;
} finally {
  await context.close();
  await browser.close();
}
