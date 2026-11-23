// usage: node stills.mjs <index.html> <out_dir> <frac> c01 c02 …   — 컷마다 (t0 + frac × dur) 시각의 기본 화면 정지 화면(1920×1080 PNG)
// 렌더 전에 캔버스 장면(scenes.js)을 눈으로 점검할 때 손으로 실행한다(make_video.py에 이 단계 명령은 없다). animatic 뒤 킷 루트에서:
//   node tools/video/stills.mjs "papers/N. name/video/work/build/index.html" "papers/N. name/video/work/stills" 0.5 c01 c02
// CHROME 환경변수가 없으면 playwright Chromium을 쓴다.
import puppeteer from 'puppeteer-core';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const [htmlArg, outDir, fracArg, ...ids] = process.argv.slice(2);
// Chrome 위치: 환경변수 CHROME(make_video.py 단계는 common.node_env()가 find_chrome 값을 넣는다. 손으로 실행할 때는 직접 지정). 없으면 playwright Chromium
import { createRequire } from 'node:module';
const CHROME = process.env.CHROME || createRequire(import.meta.url)('playwright').chromium.executablePath();
const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--allow-file-access-from-files', '--hide-scrollbars'] });
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.resolve(htmlArg)).href + '?clean=1', { waitUntil: 'networkidle0', timeout: 120000 });
await page.waitForFunction('window.OPENER && window.OPENER.ready', { timeout: 120000 });
fs.mkdirSync(outDir, { recursive: true });
for (const id of ids) {
  const t = await page.evaluate((id, f) => { const c = DATA.cuts.find(q => q.id === id); if (!c) return null; const t = c.t0 + c.dur * f; window.OPENER.seek(t); return t; }, id, Number(fracArg));
  if (t === null) { console.log('없는 컷', id); continue; }
  const el = await page.$('canvas');
  await el.screenshot({ path: path.join(outDir, `${id}.png`) });
  console.log(id, t.toFixed(2));
}
await browser.close();
