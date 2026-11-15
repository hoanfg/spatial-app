// Read-only checks for the public Bao'an audit evidence. Node.js, no packages.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
const root = path.dirname(fileURLToPath(import.meta.url));
const dir = path.join(root, 'evidence/audit-2026-11-15');
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
const consolidated = fs.readFileSync(path.join(root, 'CONSOLIDATED_FIELD_EVIDENCE_2026-11.md'));
for (const section of JSON.parse(fs.readFileSync(path.join(dir, 'consolidation_index.json'), 'utf8'))) {
  const bytes = consolidated.subarray(section.start_byte, section.start_byte + section.length_bytes);
  assert.equal(bytes.length, section.length_bytes, section.source);
  assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'), section.sha256, section.source);
}
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
await import('./audit_recovered_originals.mjs');
