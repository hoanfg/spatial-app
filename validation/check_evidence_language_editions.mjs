#!/usr/bin/env node
// Audit reading-edition coverage without modifying the original evidence.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = path.join(root, 'validation/evidence');
const editions = path.join(evidence, 'reading-editions');
const strict = process.argv.includes('--strict');
const problems = [];
const absent = [];
const sourceReferences = [];
const viable = p => fs.existsSync(p) && fs.statSync(p).isFile();
const read = p => fs.readFileSync(p, 'utf8');
const relative = p => path.relative(root, p).replaceAll(path.sep, '/');

function readingEdition(location, language, marker, label) {
  if (!viable(location)) {
    absent.push(relative(location));
    return;
  }
  const text = read(location);
  if (text.includes('—')) problems.push(`${relative(location)}: Unicode em dash found`);
  if (!text.includes(marker)) problems.push(`${relative(location)}: original SHA-256 not cited`);
  if (text.trim().length < 200) problems.push(`${relative(location)}: suspiciously short reading edition`);
  if (/\b(TODO|TBD|PLACEHOLDER|TRANSLATE ME)\b/i.test(text)) problems.push(`${relative(location)}: unfinished marker`);
  if (language === 'vi' && !/[ăâđêôơưàáạảãằắặẳẵầấậẩẫèéẹẻẽềếệểễìíịỉĩòóọỏõồốộổỗờớợởỡùúụủũừứựửữỳýỵỷỹ]/i.test(text))
    problems.push(`${relative(location)}: no Vietnamese diacritics`);
  sourceReferences.push({ label, language, file: relative(location) });
}

const manifest = JSON.parse(read(path.join(evidence, 'audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_EVIDENCE_MANIFEST_2026-11-15.json')));
const editionManifest = JSON.parse(read(path.join(editions, 'translation_manifest.json')));
const recoveredLinks = new Map(editionManifest.recovered_reports.map(entry => [entry.source_id, entry]));
const historicalLinks = new Map(editionManifest.historical_sources.map(entry => [entry.source_id, entry]));
const original = read(path.join(evidence, 'audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md'));
const matches = [...original.matchAll(/^## Source (\d{3}): `([^\r\n]+)`\r?\n\r?\n\*\*Original bytes:\*\* ([\d,]+) · \*\*SHA-256:\*\* `([a-f0-9]{64})`/gm)];
if (matches.length !== 78) problems.push(`expected 78 recovered originals, found ${matches.length}`);
for (const [index, match] of matches.entries()) {
  const number = String(index + 1).padStart(3, '0');
  if (match[1] !== number) problems.push(`source numbering gap at ${number}`);
  const [source, sha] = [match[2], match[4]];
  const [outer, inner] = source.split('::');
  const linked = inner
    ? manifest.embedded_zip_members.some(x => x.outer_archive_path === outer && x.member_path === inner && x.member_sha256 === sha)
    : manifest.source_files.some(x => x.archive_path === outer && x.sha256 === sha);
  if (!linked) problems.push(`source ${number}: manifest provenance mismatch`);
  const link = recoveredLinks.get(number);
  if (!link || link.sha256 !== sha) {
    problems.push(`source ${number}: missing or incorrect edition manifest mapping`);
    continue;
  }
  for (const lang of ['en', 'vi']) {
    const file = path.join(editions, link[lang === 'en' ? 'english' : 'vietnamese']);
    readingEdition(file, lang, sha, `recovered ${number}`);
  }
}

const history = JSON.parse(read(path.join(evidence, 'historical_document_sources_index.json')));
if (history.length !== 13) problems.push(`expected 13 historical documents, found ${history.length}`);
history.forEach((record, i) => {
  const number = String(i + 1).padStart(2, '0');
  const link = historicalLinks.get(number);
  if (!link || link.sha256 !== record.sha256) {
    problems.push(`historical source ${number}: missing or incorrect edition manifest mapping`);
    return;
  }
  for (const lang of ['en', 'vi']) {
    const pairSourceId = (link.canonical_id === '01' || link.canonical_id === '03')
      ? (lang === 'en' ? link.canonical_id : String(Number(link.canonical_id) + 1).padStart(2, '0'))
      : number;
    const pairRecord = historicalLinks.get(pairSourceId);
    const expectedSha = pairRecord?.sha256;
    if (!expectedSha) { problems.push(`historical source ${number}: missing paired provenance`); continue; }
    readingEdition(path.join(editions, link[lang === 'en' ? 'english' : 'vietnamese']),
      lang, expectedSha, `historical ${number}`);
  }
});

for (const lang of ['en', 'vi']) {
  const file = path.join(evidence, `CONSOLIDATED_FIELD_EVIDENCE_2026-11-${lang}.md`);
  if (!viable(file)) absent.push(relative(file));
  else {
    const text = read(file);
    if (text.includes('—')) problems.push(`${relative(file)}: Unicode em dash found`);
    if (text.trim().length < 1000) problems.push(`${relative(file)}: suspiciously short consolidated reading edition`);
    if (/\b(TODO|TBD|PLACEHOLDER|TRANSLATE ME)\b/i.test(text)) problems.push(`${relative(file)}: unfinished marker`);
  }
}

const expected = 78 * 2 + 13 * 2 + 2;
const count = expected - absent.length;
console.log(`Bilingual reading mappings: ${count}/${expected} source-language references resolved (${(count / expected * 100).toFixed(1)}%).`);
console.log(`Recovered reports: ${matches.length} source records; historical documents: ${history.length} source records.`);
console.log(`Missing reading editions: ${absent.length}; detected content issues: ${problems.length}.`);
for (const item of absent) console.log(`MISSING ${item}`);
for (const item of problems) console.error(`ISSUE ${item}`);
if (problems.length || (strict && absent.length)) process.exitCode = 1;
if (!strict && absent.length) console.log('Coverage is incomplete. Use --strict to fail on missing editions.');
