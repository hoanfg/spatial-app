#!/usr/bin/env node
// Check the canonical bilingual reading editions without rewriting any source evidence.
// Identical recovered report blobs are translated once and linked by their SHA-256.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = path.join(root, 'validation/evidence');
const editions = path.join(evidence, 'reading-editions');
const strict = process.argv.includes('--strict');
const issues = [];
const missing = [];
const read = p => fs.readFileSync(p, 'utf8');
const exists = p => fs.existsSync(p) && fs.statSync(p).isFile();
const relative = p => path.relative(root, p).replaceAll(path.sep, '/');
const manifestPath = path.join(editions, 'translation_manifest.json');

if (!exists(manifestPath)) {
  console.log('Bilingual translation manifest not yet published. The forensic originals remain authoritative.');
  if (strict) process.exitCode = 1;
} else {
  const manifest = JSON.parse(read(manifestPath));
  const historical = JSON.parse(read(path.join(evidence, 'historical_document_sources_index.json')));
  const recovered = JSON.parse(read(path.join(evidence, 'audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_EVIDENCE_MANIFEST_2026-11-15.json')));
  const originalText = read(path.join(evidence, 'audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md'));
  const sourceRows = [...originalText.matchAll(/^## Source (\d{3}): `([^\r\n]+)`\r?\n\r?\n\*\*Original bytes:\*\* ([\d,]+) · \*\*SHA-256:\*\* `([a-f0-9]{64})`/gm)];
  if (sourceRows.length !== 78 || manifest.recovered_reports.length !== 78)
    issues.push('Expected exactly 78 recovered source records');
  if (historical.length !== 13 || manifest.historical_sources.length !== 13)
    issues.push('Expected exactly 13 historical source records');

  const recPairs = new Map();
  for (let i = 0; i < sourceRows.length; i++) {
    const m = sourceRows[i], row = manifest.recovered_reports[i];
    if (!row || row.source_id !== m[1] || row.original_path !== m[2] ||
        row.original_bytes !== Number(m[3].replaceAll(',', '')) || row.sha256 !== m[4]) {
      issues.push(`Recovered source ${m[1]} differs from translation manifest`);
      continue;
    }
    const [outer, member] = m[2].split('::');
    const valid = member
      ? recovered.embedded_zip_members.some(f => f.outer_archive_path === outer && f.member_path === member && f.member_sha256 === m[4])
      : recovered.source_files.some(f => f.archive_path === outer && f.sha256 === m[4]);
    if (!valid) issues.push(`Recovered source ${m[1]} differs from original manifest`);
    const canonical = recPairs.get(m[4]);
    if (!canonical) recPairs.set(m[4], row.canonical_id);
    if ((canonical && canonical !== row.canonical_id) ||
        row.english !== `recovered/${row.canonical_id}-en.md` ||
        row.vietnamese !== `recovered/${row.canonical_id}-vi.md`)
      issues.push(`Recovered source ${m[1]} has inconsistent canonical translation paths`);
  }

  const historicalPairs = new Map();
  historical.forEach((record, i) => {
    const row = manifest.historical_sources[i];
    if (!row || row.source_id !== String(i + 1).padStart(2, '0') ||
        row.original_path !== record.source || row.original_bytes !== record.length_bytes ||
        row.sha256 !== record.sha256) {
      issues.push(`Historical source ${i + 1} differs from archived byte index`);
      return;
    }
    if (row.english !== `historical/${row.canonical_id}-en.md` ||
        row.vietnamese !== `historical/${row.canonical_id}-vi.md`)
      issues.push(`Historical source ${i + 1} has inconsistent edition paths`);
    if (!historicalPairs.has(row.canonical_id)) historicalPairs.set(row.canonical_id, []);
    historicalPairs.get(row.canonical_id).push(record.sha256);
  });

  const inspect = (rel, language, sourceHashes=[]) => {
    const filename = path.join(editions, rel);
    if (!exists(filename)) { missing.push(relative(filename)); return ''; }
    const s = read(filename);
    if (s.includes('—')) issues.push(`${relative(filename)}: em dash in reading edition`);
    if (s.trim().length < 200) issues.push(`${relative(filename)}: unusually short reading edition`);
    if (language === 'vi' && !/[ăâđêôơưàáạảãằắặẳẵầấậẩẫèéẹẻẽềếệểễìíịỉĩòóọỏõồốộổỗờớợởỡùúụủũừứựửữỳýỵỷỹ]/i.test(s))
      issues.push(`${relative(filename)}: no Vietnamese-language prose detected`);
    if (language === 'en' && !s.startsWith('# English') && !rel.startsWith('../'))
      issues.push(`${relative(filename)}: unexpected English edition heading`);
    if (sourceHashes.length && !sourceHashes.some(sha => s.includes(sha)))
      issues.push(`${relative(filename)}: no matching original SHA-256 in edition header/body`);
    return s;
  };

  for (const [sha, id] of recPairs) {
    inspect(`recovered/${id}-en.md`, 'en', [sha]);
    inspect(`recovered/${id}-vi.md`, 'vi', [sha]);
  }
  for (const [id, hashes] of historicalPairs) {
    const en = inspect(`historical/${id}-en.md`, 'en', hashes);
    const vi = inspect(`historical/${id}-vi.md`, 'vi', hashes);
    for (const sha of hashes)
      if (en && vi && !en.includes(sha) && !vi.includes(sha))
        issues.push(`Historical topic ${id}: source SHA-256 ${sha} missing in both editions`);
  }

  for (const language of ['en', 'vi']) {
    const f = path.join(evidence, `CONSOLIDATED_FIELD_EVIDENCE_2026-11-${language}.md`);
    if (!exists(f)) missing.push(relative(f));
    else if (read(f).includes('—')) issues.push(`${relative(f)}: em dash in reading edition`);
  }

  const required = 2 * (recPairs.size + historicalPairs.size + 1);
  const present = required - missing.length;
  console.log(`Reading editions: ${present}/${required} canonical EN/VI files.`);
  console.log(`Source records: ${sourceRows.length} recovered (${recPairs.size} distinct SHA-256 bodies), ${historical.length} historical (${historicalPairs.size} bilingual topic groups).`);
  console.log(`Missing: ${missing.length}. Mechanical problems: ${issues.length}.`);
  for (const m of missing) console.error(`MISSING ${m}`);
  for (const p of issues) console.error(`ISSUE ${p}`);
  if (issues.length || (strict && missing.length)) process.exitCode = 1;
  if (!strict && missing.length) console.log('Incomplete coverage: run with --strict to fail on missing editions.');
  console.log('Note: these structural checks do not certify line-by-line translation equivalence.');
}
