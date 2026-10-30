// Screenshot a report page in an emulated phone (or any width) through the
// Chrome DevTools Protocol. Plain `--window-size=390,...` renders blank in
// headless Chrome, so phone checks need device emulation.
//
// Usage:
//   node scripts/mobile_screenshot.mjs <page.html|url> <out.png> [options]
// Options:
//   --width 390 --height 844   viewport (width < 800 emulates a touch phone)
//   --full                     capture the whole page, not just the viewport
//   --eval "js"                run before the screenshot; its JSON-able result is printed as evalResult
//   --scroll "#selector"       scroll this element to the top of the viewport
//   --wait 4000                ms to wait after load
// Prints one JSON line: page width, overflowing elements, uncaught errors.
// Exit code 1 when the page scrolls sideways or throws.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const args = process.argv.slice(2);
const opt = (name, def) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : def; };
const [target, out] = args;
if (!target || !out) { console.error('usage: node scripts/mobile_screenshot.mjs <page> <out.png> [--width 390] [--full] [--eval js] [--scroll sel]'); process.exit(2); }
const url = /^[a-z]+:\/\//.test(target) ? target : 'file://' + resolve(target);
const W = +opt('width', 390), H = +opt('height', 844), wait = +opt('wait', 4000);
const full = args.includes('--full'), expr = opt('eval', ''), sel = opt('scroll', '');

const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const port = 9300 + Math.floor(Math.random() * 500);
const profile = mkdtempSync(join(tmpdir(), 'mshot-'));
const proc = spawn(chrome, ['--headless=new', `--remote-debugging-port=${port}`, '--disable-gpu',
  '--hide-scrollbars', `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const done = code => { proc.kill(); rmSync(profile, { recursive: true, force: true }); process.exit(code); };

let tabs;
for (let i = 0; i < 50 && !tabs; i++) {
  try { tabs = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); } catch { await sleep(200); }
}
const ws = new WebSocket(tabs.find(t => t.type === 'page').webSocketDebuggerUrl);
await new Promise(r => { ws.onopen = r; });
let seq = 0; const pending = {}; const errors = [];
ws.onmessage = m => {
  const d = JSON.parse(m.data);
  if (d.id && pending[d.id]) { pending[d.id](d); delete pending[d.id]; }
  if (d.method === 'Runtime.exceptionThrown') {
    const e = d.params.exceptionDetails; errors.push(e.exception?.description?.split('\n')[0] || e.text);
  }
};
const send = (method, params = {}) => new Promise(r => { const id = ++seq; pending[id] = r; ws.send(JSON.stringify({ id, method, params })); });
const evaluate = async expression => (await send('Runtime.evaluate', { expression, returnByValue: true })).result?.result?.value;

await send('Runtime.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 2, mobile: W < 800 });
if (W < 800) await send('Emulation.setTouchEmulationEnabled', { enabled: true });
await send('Page.navigate', { url });
await sleep(wait);
let evalResult;
if (expr) { evalResult = await evaluate(expr); await sleep(1200); }
if (sel) { await evaluate(`document.querySelector(${JSON.stringify(sel)})?.scrollIntoView({block:'start'})`); await sleep(800); }

// Elements whose right edge pokes past the viewport are what makes a page scroll sideways.
const report = JSON.parse(await evaluate(`(() => {
  const vw = document.documentElement.clientWidth, bad = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width && r.right > vw + 1 && getComputedStyle(el).position !== 'fixed') {
      let p = el.parentElement, clipped = false;
      while (p && p !== document.body) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') { clipped = true; break; } p = p.parentElement; }
      if (!clipped) bad.push((el.id ? '#' + el.id : el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\\s+/)[0] : '')) + ' right=' + Math.round(r.right));
    }
  }
  return JSON.stringify({ scrollWidth: document.documentElement.scrollWidth, viewport: vw,
    pageHeight: document.documentElement.scrollHeight, overflow: [...new Set(bad)].slice(0, 12) });
})()`));

let shot;
if (full) {
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: Math.min(report.pageHeight, 16000), deviceScaleFactor: 1, mobile: W < 800 });
  await sleep(600);
  shot = await send('Page.captureScreenshot', { format: 'png' });
} else {
  shot = await send('Page.captureScreenshot', { format: 'png' });
}
writeFileSync(out, Buffer.from(shot.result.data, 'base64'));
console.log(JSON.stringify({ out, ...report, errors, ...(evalResult !== undefined && { evalResult }) }));
done(report.scrollWidth > report.viewport || errors.length ? 1 : 0);
