// Lightweight checks for active Markdown links and math notation; no packages.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const files = [
  'README.md', 'README-vi.md',
  'docs/README.md', 'docs/README-vi.md',
  'validation/README.md', 'validation/README-vi.md',
  'validation/evidence/README.md', 'validation/evidence/README-vi.md',
  'validation/cross_location/README.md', 'validation/cross_location/README-vi.md',
  'validation/evidence/yanqing/README.md', 'validation/evidence/yanqing/README-vi.md',
];
const problems = [];
function checkBraces(math, where) {
  let depth = 0;
  for (let i = 0; i < math.length; i++) {
    if (math[i - 1] === '\\') continue;
    if (math[i] === '{') depth++;
    if (math[i] === '}') depth--;
    if (depth < 0) { problems.push(`${where}: extra } in math`); return; }
  }
  if (depth) problems.push(`${where}: unbalanced math braces`);
}
for (const file of files) {
  const raw = fs.readFileSync(path.join(root, file), 'utf8');
  if (raw.includes('—')) problems.push(`${file}: em dash must be replaced with normal punctuation`);
  const lines = raw.split(/\r?\n/);
  let inCode = false;
  let inDisplay = false;
  let displayMath = '';
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (/^\s*```/.test(line)) { inCode = !inCode; continue; }
    if (inCode) continue;
    if (line.includes('$$') && line.trim() !== '$$')
      problems.push(`${file}:${i + 1}: display-math delimiter must be on its own line`);
    const displays = (line.match(/\$\$/g) || []).length;
    for (const match of line.matchAll(/\$\$([^$]+)\$\$/g))
      checkBraces(match[1], `${file}:${i + 1}`);
    if (displays % 2) {
      if (inDisplay) { displayMath += line.split('$$')[0]; checkBraces(displayMath, `${file}:${i + 1}`); displayMath = ''; }
      else displayMath = line.split('$$')[1] || '';
      inDisplay = !inDisplay;
    } else if (inDisplay) displayMath += line;
    const withoutDisplays = line.replace(/\$\$/g, '');
    const inline = (withoutDisplays.match(/(?<!\\)\$/g) || []).length;
    if (inline % 2) problems.push(`${file}:${i + 1}: unmatched inline $`);
    for (const match of withoutDisplays.matchAll(/(?<!\\)\$([^$]+)(?<!\\)\$/g))
      checkBraces(match[1], `${file}:${i + 1}`);
    if (/\\_/.test(line)) problems.push(`${file}:${i + 1}: escaped underscore in math/text`);
    for (const match of line.matchAll(/\]\(([^)\n]+)\)/g)) {
      let target = match[1].replace(/^<|>$/g, '').split('#')[0];
      if (!target || /^[a-z][a-z\d+.-]*:/i.test(target)) continue;
      try { target = decodeURIComponent(target); } catch { /* leave literal path */ }
      if (!fs.existsSync(path.resolve(root, path.dirname(file), target)))
        problems.push(`${file}:${i + 1}: missing target ${target}`);
    }
  }
  if (inCode || inDisplay) problems.push(`${file}: unclosed code or display-math block`);
}
if (problems.length) {
  console.error(problems.join('\n'));
  process.exitCode = 1;
} else console.log(`PASS: links and basic math delimiters checked in ${files.length} active guides`);
