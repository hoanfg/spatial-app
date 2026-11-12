#!/usr/bin/env python3
"""Read-only integrity and numeric cross-check for an externally supplied Yanqing archive.

No private datasets are embedded or uploaded. This cross-check uses CSV reference
columns already present in the archive and is not a full independent rerun of
raster overlay, Earth Engine export, or Local Moran conditional simulation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

TOLERANCE = 0.00005 + 1e-9  # exported CSV: four decimal places
EXPECTED_ARCHIVE_SHA256 = "95b3874d4253eec2269f2477b648a067fb14d1c94be54bc0ed38f8795599260c"


def read_rows(archive: ZipFile, name: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(archive.read(name).decode("utf-8-sig"))))


def checked_ids(rows: list[dict[str, str]], name: str) -> set[int]:
    ids = [int(r["grid_id"]) for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate grid_id in {name}")
    return set(ids)


def abs_comparison(rows: list[dict[str, str]], left: str, right: str) -> dict:
    errors = [abs(float(r[left]) - float(r[right])) for r in rows]
    if not errors or not all(math.isfinite(e) for e in errors):
        raise ValueError(f"No finite comparison for {left}, {right}")
    return {
        "cells": len(rows),
        "within_csv_rounding": sum(e <= TOLERANCE for e in errors),
        "max_abs_error": max(errors),
        "mean_abs_error": sum(errors) / len(errors),
    }


def bh_reject(raw_p: list[float], alpha: float = 0.05) -> list[bool]:
    """Independent BH step-up implementation, using only standard Python."""
    if not all(math.isfinite(x) and 0 <= x <= 1 for x in raw_p):
        raise ValueError("Invalid p-values")
    order = sorted(range(len(raw_p)), key=lambda i: (raw_p[i], i))
    k = 0
    for position, idx in enumerate(order, 1):
        if raw_p[idx] <= alpha * position / len(order):
            k = position
    rejected = [False] * len(raw_p)
    for idx in order[:k]:
        rejected[idx] = True
    return rejected


def inspect(path: Path) -> dict:
    with ZipFile(path) as z:
        damaged = z.testzip()
        if damaged:
            raise ValueError(f"ZIP CRC failure: {damaged}")
        names = set(z.namelist())
        manifest = json.loads(z.read("EVIDENCE_MANIFEST.json"))["files"]
        if names != set(manifest) | {"EVIDENCE_MANIFEST.json"}:
            raise ValueError("ZIP contents differ from manifest")
        bad = []
        for name, record in sorted(manifest.items()):
            raw = z.read(name)
            if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
                bad.append(name)
        if bad:
            raise ValueError(f"SHA-256/size mismatch: {bad}")
        archive_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if archive_hash != EXPECTED_ARCHIVE_SHA256:
            raise ValueError("Archive SHA-256 differs from the separately recorded reference hash")

        f20 = "yanqing_viirs_all_8333_polygon_comparison.csv"
        f14 = "yanqing_2014_viirs_cell_validation.csv"
        fl = "yanqing_lisa_independent_cell_comparison.csv"
        ft = "yanqing_temporal_validation_by_cell.csv"
        rows20 = read_rows(z, f20)
        rows14 = read_rows(z, f14)
        lisa = read_rows(z, fl)
        temporal = read_rows(z, ft)
        cohorts = [checked_ids(rows, f) for rows, f in
                   [(rows20, f20), (rows14, f14), (lisa, fl), (temporal, ft)]]
        if len(cohorts[0]) != 8333 or any(cohort != cohorts[0] for cohort in cohorts[1:]):
            raise ValueError("Unexpected cell counts or missing grid_id joins")

        results20 = abs_comparison(rows20, "ntl_mean", "ntl_ref_polygon")
        results14 = abs_comparison(rows14, "ntl_2014", "ntl_2014_raster_clipped")
        if results20["within_csv_rounding"] != 8333 or results14["within_csv_rounding"] != 8333:
            raise ValueError("Raster reference cross-check did not pass CSV precision")

        active = [r for r in lisa if int(r["active_lisa"]) == 1]
        if len(active) != 7733:
            raise ValueError("Unexpected number of tested LISA cells")
        pvals = [float(r["p_exported"]) for r in active]
        rejected = bh_reject(pvals)
        bh_differences = sum(
            int(r["bh_exported"]) != int(ok) for r, ok in zip(active, rejected)
        )
        independent_seed_disagreements = sum(
            int(r["bh_exported"]) != int(r["bh_independent"]) for r in active
        )
        if bh_differences:
            raise ValueError(
                f"BH recomputation disagrees for {bh_differences} active cells"
            )

        temporal_by_id = {int(r["grid_id"]): r for r in temporal}
        disagreements = 0
        delta_errors = []
        for row in rows14:
            cell = temporal_by_id[int(row["grid_id"])]
            delta = float(row["ntl_2020"]) - float(row["ntl_2014"])
            delta_errors.append(abs(float(cell["delta_ntl"]) - delta))
            if cell["regime_export"] != row["spacetime_regime"]:
                disagreements += 1
        if max(delta_errors) > 1e-4 + 1e-9 or disagreements:
            raise ValueError("Space-Time cross-file output inconsistency")

        return {
            "archive_sha256": archive_hash,
            "manifest_files_verified": len(manifest),
            "zip_crc_passed": True,
            "viirs_2014_from_archived_reference_columns": results14,
            "viirs_2020_from_archived_reference_columns": results20,
            "lisa_active_cells": len(active),
            "bh_recomputed_significant_cells": sum(rejected),
            "bh_recomputed_disagreements": bh_differences,
            "different_seed_bh_disagreements": independent_seed_disagreements,
            "spacetime_regime_cross_file_disagreements": disagreements,
            "spacetime_max_delta_ntl_cross_file_error": max(delta_errors),
            "limitations": (
                "This checks archive integrity, archived independent reference columns, "
                "BH step-up and cross-file output consistency. It does not independently "
                "recreate raster polygons, perform a new Earth Engine export, replay "
                "the conditional LISA Monte Carlo draws, or validate GHSL/cross-location."
            ),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "archive", type=Path, help="Local, independently obtained evidence ZIP"
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()
    try:
        results = inspect(args.archive)
    except (OSError, ValueError, KeyError, EOFError, RuntimeError, BadZipFile) as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
