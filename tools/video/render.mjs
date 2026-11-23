// usage: node render.mjs <index.html> <fps> <start> <end> <out.mp4>  (무음) — 프레임마다 시간을 지정해 캡처 (frame drop 없음)
// 페이지는 window.OPENER = {ready, DURATION, seek(t)} 를 노출해야 한다 (tools/video/engine/player.html)
import puppeteer from 'puppeteer-core';
import { spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const [htmlArg, fpsArg, sArg, eArg, outArg] = process.argv.slice(2);
const ep = path.basename(outArg || 'video');
const FPS = Number(fpsArg || 30);
const FF = process.env.FFMPEG;
// Chrome 위치: make_video.py가 환경변수 CHROME에 찾아 넣는다(common.find_chrome). 없으면 playwright Chromium
import { createRequire } from 'node:module';
const CHROME = process.env.CHROME || createRequire(import.meta.url)('playwright').chromium.executablePath();
const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', protocolTimeout: 0,
  args: ['--allow-file-access-from-files', '--disable-web-security', '--hide-scrollbars', '--force-color-profile=srgb', '--enable-gpu', '--use-angle=d3d11', '--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--enable-zero-copy'] });
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.resolve(htmlArg)).href + (process.env.QS || '?clean=1'), { waitUntil: 'networkidle0', timeout: 120000 });
await page.waitForFunction('window.OPENER && window.OPENER.ready', { timeout: 120000 });
const DUR = await page.evaluate(() => window.OPENER.DURATION);
const t0 = Number(sArg || 0), t1 = Math.min(DUR, Number(eArg || DUR));
const N = Math.round((t1 - t0) * FPS);
const out = outArg;
const ff = spawn(FF, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', String(FPS), out], { stdio: ['pipe', 'inherit', 'inherit'] });
const cdp = await page.createCDPSession();
const start = Date.now();
for (let i = 0; i < N; i++) {
  const t = t0 + i / FPS;
  await page.evaluate(async t => { window.OPENER.seek(t); await new Promise(r => requestAnimationFrame(r)); }, t);
  const { data } = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 93, optimizeForSpeed: true, captureBeyondViewport: false });
  const buf = Buffer.from(data, 'base64');
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % (FPS * 10) === 0) { const el = (Date.now() - start) / 1000; console.log(`${ep} ${i}/${N} ${(i / Math.max(el, .001)).toFixed(1)} fps`); }
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log(`${ep} rendered ${N} frames in ${((Date.now() - start) / 1000).toFixed(0)}s -> ${out}`);
