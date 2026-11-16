// Verify recovered inventory and report bytes; never execute report content.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const dir = new URL('./evidence/audit-2026-11-15/recovered-originals/', import.meta.url);
const read = n => fs.readFileSync(new URL(n === 'SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md' ? n.replace(/\.md$/, '.txt') : n, dir));
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const receipt = JSON.parse(read('recovery_receipt.json'));
for (const f of receipt.files) {
  const b = read(f.name); assert.equal(b.length, f.bytes); assert.equal(hash(b), f.sha256);
}
const manifest = JSON.parse(read('SPATIAL_APP_AUDIT_EVIDENCE_MANIFEST_2026-11-15.json'));
const md = read('SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.txt');
assert.equal(hash(md), manifest.markdown_verbatim_sha256);
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
const text = md.toString('utf8');
const regex = /^## Source (\d{3}): `([^\r\n]+)`\r?\n\r?\n\*\*Original bytes:\*\* ([\d,]+) · \*\*SHA-256:\*\* `([a-f0-9]{64})` · \*\*Origin:\*\* ([^\r\n]+)\r?\n\r?\n<!-- BEGIN ORIGINAL SOURCE (\d{3}) -->\r?\n/gm;
let count = 0;
for (const m of text.matchAll(regex)) {
  assert.equal(Number(m[1]), ++count); assert.equal(m[1], m[6]);
  const start = Buffer.byteLength(text.slice(0, m.index + m[0].length));
  const length = Number(m[3].replaceAll(',', ''));
  const body = md.subarray(start, start + length); assert.equal(body.length, length); assert.equal(hash(body), m[4]);
  const [outer, member] = m[2].split('::');
  const ref = member ? manifest.embedded_zip_members.find(f => f.outer_archive_path === outer && f.member_path === member)
    : manifest.source_files.find(f => f.archive_path === outer);
  assert.ok(ref, m[2]);
  assert.equal(member ? ref.member_bytes : ref.size_bytes, length);
  assert.equal(member ? ref.member_sha256 : ref.sha256, m[4]);
}
assert.equal(count, 78);
for (const [local, basename] of [['baoan_ntl_2020_500m.csv', 'bao_an_NTL_2020_500m(1).csv'], ['spatial_app_performance.json', 'spatial_app_performance.json']]) {
  const bytes = fs.readFileSync(new URL('../' + local, dir));
  const matches = manifest.source_files.filter(f => f.basename === basename);
  assert.ok(matches.some(f => f.size_bytes === bytes.length && f.sha256 === hash(bytes)));
}
console.log('PASS: original manifest/CSV agree on 118 records; 78 report bodies match original manifest; two published field files match original hashes. 271 ZIP member records indexed, archive bytes NOT verified.');
