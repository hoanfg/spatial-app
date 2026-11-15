#!/usr/bin/env python3
"""Verify every captured evidence file and each verbatim Markdown byte range."""
import hashlib, io, json, zipfile, sys
from pathlib import Path

def sha(data): return hashlib.sha256(data).hexdigest()

def run(path):
    z=zipfile.ZipFile(path)
    bad=z.testzip()
    if bad: raise AssertionError('Bad ZIP entry: '+bad)
    manifest=json.loads(z.read('00_INDEX/AUDIT_EVIDENCE_MANIFEST.json'))
    for source in manifest['source_files']:
        got=z.read(source['archive_path'])
        assert len(got)==source['size_bytes'],source['archive_path']
        assert sha(got)==source['sha256'],source['archive_path']
    for f in manifest['embedded_zip_members']:
        with zipfile.ZipFile(io.BytesIO(z.read(f['outer_archive_path']))) as original:
            inner=original.read(f['member_path'])
        assert len(inner)==f['member_bytes'],f['member_path']
        assert sha(inner)==f['member_sha256'],f['member_path']
        assert inner==z.read(f['expanded_archive_path']),f['expanded_archive_path']
    md=z.read('01_CONSOLIDATED_MARKDOWN/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md')
    mdref=json.loads(z.read('00_INDEX/MARKDOWN_BYTE_RANGES.json'))
    assert sha(md)==mdref['consolidated_sha256']
    for x in mdref['byte_ranges']:
        original=x['source']
        if '::' in original:
            outer,member=original.split('::',1)
            with zipfile.ZipFile(io.BytesIO(z.read(outer))) as nested:
                raw=nested.read(member)
        else:
            raw=z.read(original)
        off,n=x['start_byte'],x['original_byte_length']
        assert raw==md[off:off+n],original
        assert sha(raw)==x['original_sha256'],original
    print(f"VERIFIED {len(manifest['source_files'])} files, {len(manifest['embedded_zip_members'])} nested files, {len(mdref['byte_ranges'])} verbatim MD segments")

if __name__=='__main__':
    run(sys.argv[1] if len(sys.argv)>1 else 'SPATIAL_APP_FULL_AUDIT_EVIDENCE_2026-11-15.zip')
