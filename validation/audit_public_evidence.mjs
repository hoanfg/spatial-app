// Read-only checks for the public Bao'an audit evidence. Node.js, no packages.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
const root = path.dirname(fileURLToPath(import.meta.url));
const dir = path.join(root, 'evidence/audit-2026-11-15');
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
for (const f of manifest.files) {
  const bytes = fs.readFileSync(path.join(dir, f.name));
  assert.equal(bytes.length, f.bytes, f.name);
  assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'), f.sha256, f.name);
}
function parseCSV(text) {
  const rows = []; let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') { if (quoted && text[i + 1] === '"') { field += '"'; i++; } else quoted = !quoted; }
    else if (c === ',' && !quoted) { row.push(field); field = ''; }
    else if (c === '\n' && !quoted) { row.push(field.replace(/\r$/, '')); rows.push(row); row = []; field = ''; }
    else field += c;
  }
  assert.equal(quoted, false, 'Unclosed CSV quote');
  if (field || row.length) { row.push(field.replace(/\r$/, '')); rows.push(row); }
  const header = rows.shift();
  return rows.map(r => { assert.equal(r.length, header.length); return Object.fromEntries(header.map((h, i) => [h.replace(/^\uFEFF/, ''), r[i]])); });
}
const rows = parseCSV(fs.readFileSync(path.join(dir, 'baoan_ntl_2020_500m.csv'), 'utf8'));
assert.equal(rows.length, 7148);
assert.equal(new Set(rows.map(r => r.grid_id)).size, rows.length);
const quality = ['dq_observed_fraction','dq_negative_fraction','dq_zero_fraction','dq_mean_valid_months','dq_low_month_fraction'];
for (const r of rows) {
  assert.equal(r.year, '2020'); assert.equal(r.cell_size_m, '500');
  assert.equal(r.dq_status, 'observed'); assert.equal(r.dq_ntl_policy, 'legacy_zero_fill');
  assert.equal(r.dq_stat_missing.toLowerCase(), 'false');
  for (const key of quality) assert.ok(r[key] !== '' && Number.isFinite(Number(r[key])), key);
  for (const key of quality.filter(k => k !== 'dq_mean_valid_months')) assert.ok(Number(r[key]) >= 0 && Number(r[key]) <= 1);
  assert.ok(Number(r.dq_mean_valid_months) >= 0 && Number(r.dq_mean_valid_months) <= 12);
}
const support = rows.map(r => Number(r.dq_mean_valid_months));
const perf = JSON.parse(fs.readFileSync(path.join(dir, 'spatial_app_performance.json'), 'utf8'));
assert.equal(perf.schema, 'spatial_app_perf_v1'); assert.equal(perf.pipeline_success, true);
assert.ok(perf.stages.every(s => s.status === 'ok'));
const a02 = perf.stages.find(s => s.stage === 'a02.cell_quality'); assert.ok(a02);
const result = {rows: rows.length, unique_grid_ids: rows.length, observed_rows: rows.filter(r => r.dq_status === 'observed').length,
  mean_valid_months: {min: Math.min(...support), max: Math.max(...support), mean: support.reduce((a,b)=>a+b,0)/support.length},
  pipeline_wall_time_s: perf.pipeline_wall_time_s, a02_wall_time_s: a02.wall_time_s,
  sampled_process_peak_mib: perf.sampled_process_peak_mib,
  limitations: ['CSV integrity/semantics check only; no fresh Earth Engine or raster-overlay run.', 'No pre-fix CSV available for unchanged-NTL comparison.', 'Profiler has no commit identity; this is the historical pre-optimization baseline, not a measured PR #27 speedup.']};
if (process.argv.includes('--check-result')) assert.deepEqual(result, JSON.parse(fs.readFileSync(path.join(dir, 'verified_summary.json'), 'utf8')));
console.log(JSON.stringify(result, null, 2));
const postDir = path.join(root, 'evidence/a02_post_pr27');
const postRows = parseCSV(fs.readFileSync(path.join(postDir, 'CHN_guangdong_shenzhen_bao_an_2020_500m_lisa_cells.csv'), 'utf8'));
assert.equal(postRows.length, rows.length);
const sharedColumns = Object.keys(rows[0]);
for (let i = 0; i < rows.length; i++) {
  for (const key of sharedColumns) assert.equal(postRows[i][key], rows[i][key], `row ${i}, column ${key}`);
}
const postPerf = JSON.parse(fs.readFileSync(path.join(postDir, 'spatial_app_performance.json'), 'utf8'));
assert.equal(postPerf.schema, 'spatial_app_perf_v1');
assert.equal(postPerf.pipeline_success, true);
assert.ok(postPerf.stages.every(s => s.status === 'ok'));
const postA02 = postPerf.stages.find(s => s.stage === 'a02.cell_quality'); assert.ok(postA02);
console.log(`PASS: ${rows.length} Bao'an rows match across all ${sharedColumns.length} shared columns; the later export adds analysis columns without changing the shared values. Later pipeline ${postPerf.pipeline_wall_time_s}s, A02 ${postA02.wall_time_s}s, sampled peak ${postPerf.sampled_process_peak_mib} MiB.`);

const yanqingDir = path.join(root, 'evidence/yanqing');
const viirsRows = parseCSV(fs.readFileSync(path.join(yanqingDir, 'yanqing_viirs_all_8333_polygon_comparison.csv'), 'utf8'));
assert.equal(viirsRows.length, 8333);
const viirsErrors = viirsRows.map(r => Number(r.abs_error));
const viirsWithinTolerance = viirsErrors.filter(v => v <= 0.00005).length;
assert.equal(viirsWithinTolerance, 8332);
const viirsMaxError = Math.max(...viirsErrors);
const viirsMeanError = viirsErrors.reduce((a, b) => a + b, 0) / viirsErrors.length;
const viirsOutliers = viirsRows.filter(r => Number(r.abs_error) > 0.00005);
assert.equal(viirsOutliers.length, 1);
assert.equal(viirsOutliers[0].grid_id, '349');
assert.equal(viirsOutliers[0].is_border_cell, '1');

const lisaRows = parseCSV(fs.readFileSync(path.join(yanqingDir, 'yanqing_lisa_independent_cell_comparison.csv'), 'utf8'));
assert.equal(lisaRows.length, 8333);
const lisaClassMatches = lisaRows.filter(r => r.class_independent === r.class_exported).length;
const lisaActive = lisaRows.filter(r => r.active_lisa === '1').length;
assert.equal(lisaClassMatches, 8154);
assert.equal(lisaActive, 7733);

const spaceTimeRows = parseCSV(fs.readFileSync(path.join(yanqingDir, 'CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv'), 'utf8'));
assert.equal(spaceTimeRows.length, 8333);
const regimes = Object.fromEntries([...new Set(spaceTimeRows.map(r => r.spacetime_regime))].sort().map(
  regime => [regime, spaceTimeRows.filter(r => r.spacetime_regime === regime).length]
));
assert.deepEqual(regimes, {
  '1_Synergistic_Growth': 1456,
  '2_Agglomeration_Shadow': 75,
  '3_Emergent_Pioneer': 194,
  '4_Synchronized_Decline': 4711,
  'Excluded_or_Static': 1897,
});
const ntl2014 = spaceTimeRows.map(r => Number(r.ntl_2014));
const ntl2020 = spaceTimeRows.map(r => Number(r.ntl_2020));
const mean = values => values.reduce((a, b) => a + b, 0) / values.length;
assert.ok(Math.abs(mean(ntl2014) - 0.44515832233289426) < 1e-12);
assert.ok(Math.abs(mean(ntl2020) - 1.4137191407656382) < 1e-12);
const increases = spaceTimeRows.filter(r => Number(r.ntl_2020) > Number(r.ntl_2014)).length;
const decreases = spaceTimeRows.filter(r => Number(r.ntl_2020) < Number(r.ntl_2014)).length;
const synchronized = spaceTimeRows.filter(r => r.spacetime_regime === '4_Synchronized_Decline');
const synchronizedIncreases = synchronized.filter(r => Number(r.ntl_2020) > Number(r.ntl_2014)).length;
assert.equal(increases, 8221);
assert.equal(decreases, 112);
assert.equal(synchronizedIncreases, 4624);
console.log(`PASS: Yanqing VIIRS ${viirsWithinTolerance}/8333 within 0.00005 (mean ${viirsMeanError}, max ${viirsMaxError}); LISA class matches ${lisaClassMatches}/8333 with ${lisaActive} active cells; Space-Time regime counts and absolute NTL changes agree (${increases} up, ${decreases} down; ${synchronizedIncreases}/4711 synchronized-decline cells increased).`);
await import('./audit_evidence_inventory.mjs');
