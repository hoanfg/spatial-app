// Preserve superseded narrative documents byte-for-byte in one indexed archive.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const archivePath = path.join(root, 'validation/evidence/historical_document_sources_2026-11-15.txt');
const indexPath = path.join(root, 'validation/evidence/historical_document_sources_index.json');
const sources = [
  'docs/GADM_v41 pipeline specification.md',
  'docs/GADM_v41-vi pipeline specification.md',
  'docs/VALIDATION MASTER.md',
  'docs/VALIDATION MASTER-vi.md',
  'docs/audit-fixes-2026-11-11.md',
  'docs/spacetime-relative-regime-interpretation.md',
  'validation/A02_POST_OPTIMIZATION_FIELD_2026-11-15.md',
  'validation/A02_PR_PROPOSAL.md',
  'validation/ADVANCED_STATISTICAL_VALIDATION_A03B.md',
  'validation/DATA_SEMANTICS_A02.md',
  'validation/INTEGRATION_AUDIT_2026-11-11-vi.md',
  'validation/MAJOR_REVIEW_COVERAGE_EVIDENCE_2026-11.md',
  'validation/NUMERICAL_VALIDATION_A03.md',
];
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

if (process.argv.includes('--build')) {
  const parts = [];
  const index = [];
  let length = 0;
  const add = bytes => { parts.push(bytes); length += bytes.length; };
  add(Buffer.from('# Historical document sources — 15 November 2026\n\nThese are original document bytes retained for audit provenance. Current guidance is in the README pairs at the repository root, docs/ and validation/. Time-specific pending statements below are historical.\n\n', 'utf8'));
  for (const source of sources) {
    const bytes = fs.readFileSync(path.join(root, source));
    add(Buffer.from(`---\n\n## Source: ${source}\n\n<!-- BEGIN ORIGINAL -->\n`, 'utf8'));
    index.push({ source, start_byte: length, length_bytes: bytes.length, sha256: digest(bytes) });
    add(bytes);
    add(Buffer.from('\n<!-- END ORIGINAL -->\n\n', 'utf8'));
  }
  fs.writeFileSync(archivePath, Buffer.concat(parts));
  fs.writeFileSync(indexPath, JSON.stringify(index, null, 2) + '\n');
}

const archive = fs.readFileSync(archivePath);
const index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
assert.equal(index.length, sources.length);
for (const section of index) {
  assert.ok(sources.includes(section.source));
  const bytes = archive.subarray(section.start_byte, section.start_byte + section.length_bytes);
  assert.equal(bytes.length, section.length_bytes, section.source);
  assert.equal(digest(bytes), section.sha256, section.source);
}
console.log(`PASS: ${index.length} original documents preserved in one indexed archive`);
