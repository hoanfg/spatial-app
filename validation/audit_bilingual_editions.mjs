// Validate bilingual reading coverage without altering forensic source archives.
// Node.js built-ins only; run from any working directory.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = path.join(root, 'validation/evidence');
const editions = path.join(evidence, 'reading-editions');
const manifest = JSON.parse(fs.readFileSync(path.join(editions, 'translation_manifest.json'), 'utf8'));
const historicalIndex = JSON.parse(fs.readFileSync(path.join(evidence, 'historical_document_sources_index.json'), 'utf8'));
const recoveredRaw = fs.readFileSync(path.join(evidence, 'audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md'), 'utf8');
const reports = [...recoveredRaw.matchAll(/^## Source (\d{3}): `([^\r\n]+)`\r?\n\r?\n\*\*Original bytes:\*\* ([\d,]+) · \*\*SHA-256:\*\* `([a-f0-9]{64})` · \*\*Origin:\*\* ([^\r\n]+)/gm)];
const problems = [];
const requireFile = relative => {
  const full = path.join(editions, relative);
  if (!fs.existsSync(full)) problems.push(`Missing bilingual reading file: ${relative}`);
  return full;
};
const seenSHA = new Map();
assert.equal(manifest.schema, 'spatial_app_bilingual_evidence_reading_editions_v1');
assert.equal(manifest.recovered_reports.length, 78);
assert.equal(reports.length, 78);
assert.equal(manifest.historical_sources.length, historicalIndex.length);
assert.equal(historicalIndex.length, 13);
for (let n = 0; n < reports.length; n++) {
  const m = reports[n], x = manifest.recovered_reports[n];
  assert.equal(x.source_id, m[1]);
  assert.equal(x.original_path, m[2]);
  assert.equal(x.original_bytes, Number(m[3].replaceAll(',', '')));
  assert.equal(x.sha256, m[4]);
  assert.equal(x.origin, m[5]);
  if (!seenSHA.has(m[4])) seenSHA.set(m[4], m[1]);
  assert.equal(x.canonical_id, seenSHA.get(m[4]));
  assert.equal(x.english, `recovered/${x.canonical_id}-en.md`);
  assert.equal(x.vietnamese, `recovered/${x.canonical_id}-vi.md`);
}
assert.equal(seenSHA.size, 35);
assert.equal(manifest.unique_recovered_report_count, seenSHA.size);
const historicalGroups = new Set();
for (let n = 0; n < historicalIndex.length; n++) {
  const record = historicalIndex[n], x = manifest.historical_sources[n], group = String(n === 1 ? 1 : n === 3 ? 3 : n + 1).padStart(2, '0');
  assert.equal(x.source_id, String(n + 1).padStart(2, '0'));
  assert.equal(x.original_path, record.source);
  assert.equal(x.original_bytes, record.length_bytes);
  assert.equal(x.sha256, record.sha256);
  assert.equal(x.canonical_id, group);
  historicalGroups.add(group);
  assert.equal(x.english, `historical/${group}-en.md`);
  assert.equal(x.vietnamese, `historical/${group}-vi.md`);
}
assert.equal(historicalGroups.size, 11);
const canonicalEntries = [
  ...[...seenSHA.entries()].map(([sha, id]) => ({group:'recovered', id, sha})),
  ...[...historicalGroups].map(id => ({group:'historical', id})),
];
const allFiles = new Set();
for (const item of canonicalEntries) {
  for (const lang of ['en', 'vi']) {
    const relative = `${item.group}/${item.id}-${lang}.md`;
    const full = requireFile(relative);
    allFiles.add(relative);
    if (!fs.existsSync(full)) continue;
    const content = fs.readFileSync(full, 'utf8');
    if (content.includes('—')) problems.push(`${relative}: Unicode em dash in editorial edition`);
    if (item.sha && !content.includes(item.sha)) problems.push(`${relative}: missing original SHA-256`);
    if (!/^# /m.test(content)) problems.push(`${relative}: no document heading`);
  }
}
for (const relative of [
  'README.md', 'README-vi.md', 'recovered/README.md', 'recovered/README-vi.md',
  'historical/README.md', 'historical/README-vi.md',
  '../CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md',
  '../CONSOLIDATED_FIELD_EVIDENCE_2026-11-vi.md',
]) {
  const full = requireFile(relative); allFiles.add(relative);
  if (fs.existsSync(full) && fs.readFileSync(full, 'utf8').includes('—'))
    problems.push(`${relative}: Unicode em dash in editorial edition`);
}
// Validate reader navigation links. Original-source body links from archived documents
// can point to now-superseded paths; only editorial navigation and the six
// newly written indexes are required to be current repository-local links.
for (const relative of allFiles) {
  const full = path.join(editions, relative);
  if (!fs.existsSync(full)) continue;
  const s = fs.readFileSync(full, 'utf8');
  const isIndex = /(^|\/)README(-vi)?\.md$/.test(relative);
  const section = isIndex ? s : s.split(/\n---\n/)[0];
  for (const m of section.matchAll(/\]\(([^)\n]+)\)/g)) {
    const target = m[1].split('#')[0].trim().replace(/^<|>$/g,'');
    if (!target || /^(?:[a-z][a-z\d+.-]*:|#|\/)/i.test(target)) continue;
    let decoded = target;
    try {decoded = decodeURIComponent(target);} catch {/* leave unchanged */}
    if (!fs.existsSync(path.resolve(path.dirname(full), decoded)))
      problems.push(`${relative}: broken navigation link ${target}`);
  }
}
if (problems.length) {
  console.error(problems.join('\n'));
  process.exitCode = 1;
} else {
  console.log(`PASS: ${reports.length} recovered source entries / ${seenSHA.size} unique bilingual report pairs; ${historicalIndex.length} historical sources / ${historicalGroups.size} bilingual pairs; consolidated EN/VI; editorial punctuation and index links`);
}
