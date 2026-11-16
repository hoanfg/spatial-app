// Verify the recovered inventories and the selected public field files.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const dir = new URL('./evidence/audit-2026-11-15/recovered-originals/', import.meta.url);
const read = n => fs.readFileSync(new URL(n, dir));
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const manifest = JSON.parse(read('SPATIAL_APP_AUDIT_EVIDENCE_MANIFEST_2026-11-15.json'));
assert.equal(manifest.source_files.length, 118); assert.equal(manifest.embedded_zip_members.length, 271);
assert.equal(new Set(manifest.source_files.map(f => f.archive_path)).size, 118);
assert.equal(new Set(manifest.embedded_zip_members.map(f => f.expanded_archive_path)).size, 271);
const rows = read('SPATIAL_APP_AUDIT_FILE_MANIFEST_2026-11-15.csv').toString('utf8').trim().split(/\r?\n/);
assert.equal(rows.shift(), 'archive_path,kind,basename,extension,size_bytes,sha256');
assert.equal(rows.length, 118);
for (const line of rows) {
  // This fixed received inventory has no quoted/comma-containing fields.
  const values = line.split(','); assert.equal(values.length, 6);
  const [p, kind, basename, extension, size, sha] = values;
  const f = manifest.source_files.find(f => f.archive_path === p); assert.ok(f);
  assert.deepEqual([f.kind, f.basename, f.extension, f.size_bytes, f.sha256], [kind, basename, extension, Number(size), sha]);
}
for (const [local, basename] of [['baoan_ntl_2020_500m.csv', 'bao_an_NTL_2020_500m(1).csv'], ['spatial_app_performance.json', 'spatial_app_performance.json']]) {
  const bytes = fs.readFileSync(new URL('../' + local, dir));
  const matches = manifest.source_files.filter(f => f.basename === basename);
  assert.ok(matches.some(f => f.size_bytes === bytes.length && f.sha256 === hash(bytes)));
}
console.log('PASS: JSON and CSV inventories agree on 118 direct records; two published field files match recorded hashes. 271 ZIP-member records are indexed, but the private archive and removed verbatim report compilation are not verified here.');
