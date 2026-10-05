/** Record the actual public MVP in an isolated media-processing browser.
 * The fresh study ZIP stays in the work directory; only the final video is shared.
 * Requires Playwright with Chromium and Python 3.12 for the exact rerun.
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

async function main() {
  const dir = path.resolve(process.argv[2] || 'demo-recording');
  fs.mkdirSync(dir, { recursive: true });
  const meta = { url: 'https://solana-quant.hkakasi358.workers.dev/audit/', stages: {}, complete: false };
  const save = () => fs.writeFileSync(path.join(dir, 'recording.json'), JSON.stringify(meta, null, 2));
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({ viewport: { width: 1280, height: 650 }, recordVideo: { dir, size: { width: 1280, height: 650 } }, acceptDownloads: true, reducedMotion: 'reduce' });
  const start = Date.now();
  const page = await context.newPage();
  const mark = (name) => { meta.stages[name] = (Date.now() - start) / 1000; save(); console.log(JSON.stringify({ stage: name, at: meta.stages[name] })); };
  const pause = (ms) => page.waitForTimeout(ms);
  const show = async (locator, ms = 4500) => { await locator.scrollIntoViewIfNeeded(); await pause(ms); };
  const top = async () => { await page.getByRole('region', { name: 'Your next audit step' }).scrollIntoViewIfNeeded(); await pause(900); };
  const click = async (locator) => { await locator.scrollIntoViewIfNeeded(); const box = await locator.boundingBox(); if (box) await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 18 }); await pause(350); await locator.click(); };
  try {
    await page.goto(meta.url, { waitUntil: 'networkidle', timeout: 90000 });
    await page.getByRole('heading', { name: 'Put your hypothesis to the test.' }).waitFor({ timeout: 90000 });
    await page.getByRole('checkbox', { name: 'Offline audit · keep this attempt and its lock on this device' }).check();
    await page.getByRole('button', { name: 'Inspect training vs benchmarks', exact: true }).first().waitFor({ state: 'visible', timeout: 90000 });
    await page.evaluate(() => {
      const cursor = document.createElement('div');
      cursor.style.cssText = 'position:fixed;width:14px;height:14px;border-radius:50%;border:2px solid #8befc4;box-shadow:0 0 0 5px #8befc433;pointer-events:none;z-index:99999;left:900px;top:90px';
      document.body.appendChild(cursor);
      document.addEventListener('mousemove', e => { cursor.style.left = `${e.clientX - 7}px`; cursor.style.top = `${e.clientY - 7}px`; });
    });
    mark('intro'); await pause(9000);
    mark('setup');
    const setup = page.locator('summary').filter({ hasText: 'Review or edit study setup' });
    await click(setup);
    await show(page.getByRole('heading', { name: 'Hypothesis & universe' }));
    await show(page.getByRole('heading', { name: 'Training configuration' }));
    await click(setup); await top();
    mark('training_start'); await click(page.getByRole('button', { name: 'Inspect training vs benchmarks', exact: true }).first());
    await page.getByRole('button', { name: 'Read training results', exact: true }).waitFor({ timeout: 240000 });
    await page.getByRole('button', { name: 'Read training results', exact: true }).waitFor({ state: 'visible' });
    await page.waitForFunction(() => !document.querySelector('.evidence-jump')?.disabled, null, { timeout: 240000 });
    mark('training_result'); await click(page.getByRole('button', { name: 'Read training results', exact: true })); await pause(7000);
    await show(page.getByRole('heading', { name: 'Training-only sensitivity · all seven rows', exact: true }), 6500);
    await top(); mark('freeze_start'); await click(page.getByRole('button', { name: 'Freeze this configuration', exact: true }));
    await page.getByRole('heading', { name: 'This snapshot is locked' }).waitFor({ timeout: 60000 });
    const manifest = page.locator('summary').filter({ hasText: 'Immutable experiment manifest' });
    await show(page.getByRole('heading', { name: 'This snapshot is locked' }), 2500);
    await click(manifest); await pause(5500); await click(manifest); await top();
    mark('holdout_start'); await click(page.getByRole('button', { name: 'Evaluate locked historical holdout', exact: true }));
    await page.getByRole('button', { name: 'Read the final result', exact: true }).waitFor({ timeout: 180000 });
    await page.waitForFunction(() => !document.querySelector('.evidence-jump')?.disabled, null, { timeout: 180000 });
    mark('holdout_result'); await click(page.getByRole('button', { name: 'Read the final result', exact: true })); await pause(6000);
    const holdout = page.locator('#holdout-results');
    await show(holdout.getByRole('heading', { name: 'Same period. Three portfolios.', exact: true }), 6500);
    await show(holdout.getByRole('heading', { name: 'The full comparison', exact: true }), 6500);
    const table = await holdout.locator('table').innerText();
    meta.reference_values_visible = ['1.28', '1.92', '4.24', '8.88'].every(x => table.includes(x));
    if (!meta.reference_values_visible) throw new Error('Actual holdout differs from the documented unchanged reference; review before sharing.');
    mark('trade'); await holdout.getByLabel('Inspect portfolio').selectOption('strategy');
    await holdout.getByLabel('Inspect a trade').selectOption({ index: 1 });
    await show(holdout.getByRole('heading', { name: 'One modeled trade', exact: true }), 6500);
    const trade = holdout.locator('summary').filter({ hasText: 'Exact trade record and cost components' });
    await click(trade); await pause(5500); await top();
    mark('export_start');
    const pending = page.waitForEvent('download', { timeout: 240000 });
    await click(page.getByRole('button', { name: 'Download reproduction ZIP', exact: true }).first());
    const download = await pending;
    const archive = path.join(dir, 'fresh-reproduction.zip');
    await download.saveAs(archive);
    const failure = await download.failure(); if (failure) throw new Error(failure);
    meta.download_bytes = fs.statSync(archive).size;
    mark('export_complete'); await pause(5000);
    const python = `import json,subprocess,sys,zipfile\nfrom pathlib import Path\nr=Path(sys.argv[1]);out=r/'reproduction';out.mkdir(exist_ok=True)\nwith zipfile.ZipFile(r/'fresh-reproduction.zip') as z:\n for n in z.namelist():\n  p=(out/n).resolve()\n  assert p.is_relative_to(out.resolve()),'Unsafe archive path'\n z.extractall(out)\nf=next(out.rglob('reproduce.py'));p=subprocess.run([sys.executable,str(f)],cwd=f.parent,capture_output=True,text=True,timeout=150)\nassert p.returncode==0,p.stderr+p.stdout\na=json.loads(p.stdout);assert a.get('reproduced') is True,a\nprint(json.dumps(a))`;
    const reproductionPython = process.env.QUANT_REPRO_PYTHON || 'python3.12';
    meta.reproduction_python = execFileSync(reproductionPython, ['--version'], { encoding: 'utf8' }).trim();
    meta.reproduction = JSON.parse(execFileSync(reproductionPython, ['-c', python, dir], { encoding: 'utf8', timeout: 170000 }));
    mark('reproduction_proof');
    const escape = x => String(x).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
    await page.setContent(`<html><body style="margin:0;background:#10171c;color:#edf5f2;font:22px sans-serif;padding:40px"><p style="color:#8befc4;font-size:15px;letter-spacing:2px">VERIFICATION REPORT · ACTUAL CLI OUTPUT</p><h1 style="font-size:32px">Independent check of this exported ZIP</h1><p style="color:#b7c5c7">${escape(meta.reproduction_python)} · python3.12 reproduce.py · ${meta.download_bytes.toLocaleString('en-US')} bytes</p><pre style="background:#17242a;padding:24px;font-size:16px;white-space:pre-wrap;overflow-wrap:anywhere">${escape(JSON.stringify(meta.reproduction, null, 2))}</pre><p style="color:#8befc4;font-size:16px">This report renders the completed Python run. It is not an application screen or a simulated terminal.</p></body></html>`);
    await pause(12000); mark('end');
    meta.complete = true; save();
  } catch (error) {
    meta.error = String(error); save();
    await page.screenshot({ path: path.join(dir, 'error.jpg'), type: 'jpeg', quality: 70 }).catch(() => {});
    throw error;
  } finally {
    const video = page.video(); await context.close();
    if (video) { meta.raw_video = await video.path(); save(); }
    await browser.close();
  }
  console.log(JSON.stringify({ complete: meta.complete, raw_video: meta.raw_video, reproduced: meta.reproduction?.reproduced }));
}
main().catch(e => { console.error(e); process.exit(1); });
