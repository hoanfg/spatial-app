#!/usr/bin/env python3
"""G05: sensitivity of NTL gradients to NTL-selected city centers.

Scope:
* The synthetic experiment has a known center selected BEFORE light is drawn.
  That is a designed reference, not an observed economic CBD.
* The existing Bao'an 2020 archive permits geometry-only center comparisons
  against the production-selected center inferred from saved rounded distances.
  No external economic CBD coordinates or jobs are represented.
* Existing G04, G17, G18, A03, A02, V11 and GHSL validation stays untouched.
* No fitted in-sample R2 establishes monocentric urban economic structure.

Run in root:
 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python validation/g05_ntl_center_experiment.py --verify
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ntl.lisa_core import (  # noqa: E402
    compute_urban_density_gradient, run_lisa,
)

OUT = ROOT / "validation" / "evidence" / "g05_ntl_center"
BAOAN = (ROOT / "validation" / "evidence" / "a02_post_pr27"
         / "CHN_guangdong_shenzhen_bao_an_2020_500m_lisa_cells.csv")
SEED = 5026
CELL_M = 500.0
SIDE = 25
REPS = 80
PERMS = 999
ALPHA = 0.05
TRUE_IJ = (9.75, 13.25)
ARTIFACT_IJ = (20.5, 6.5)
ARTIFACT_SCALE_KM = 0.85
SCENARIOS = {"baseline": 0.0, "nonjob_light_60": 60.0,
             "nonjob_light_170": 170.0}
SYN_METHODS = ("known_generator_center", "production_lisa_selected",
               "geometry_only_centroid", "ntl_weighted_centroid",
               "brightest_ntl_cell")
REAL_METHODS = ("archived_ntl_selected", "geometry_only_centroid",
                "ntl_weighted_centroid", "brightest_ntl_cell")
MC_METHODS = ("known_generator_center", "geometry_only_centroid",
              "ntl_weighted_centroid", "brightest_ntl_cell")
COMP_COLS = ("source", "scenario", "center_method", "center_x_epsg_m",
             "center_y_epsg_m", "center_distance_to_reference_km",
             "reference", "gradient_gamma_per_km", "gradient_r2",
             "delta_gamma_vs_reference", "delta_r2_vs_reference",
             "n_cells_in_fit", "selection_rule", "hh_clusters_eligible")
MC_COLS = ("replicate", "scenario", "center_method",
           "distance_to_known_center_km", "gradient_gamma_per_km",
           "gradient_r2", "delta_gamma_vs_oracle",
           "delta_r2_vs_oracle")


def csv_text(rows, fields):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def number(value):
    value = float(value)
    return repr(value) if np.isfinite(value) else ""


def fround(value, ndigits=6):
    v = float(value)
    return round(v, ndigits) if np.isfinite(v) else None


def xy_distance_km(cx, cy, point):
    return np.hypot(cx - point[0], cy - point[1]) / 1000.0


def center_distance_km(a, b):
    return float(np.hypot(a[0] - b[0], a[1] - b[1]) / 1000.0)


def geometry_center(cx, cy, area):
    return (float(np.average(cx, weights=area)),
            float(np.average(cy, weights=area)))


def mass_center(cx, cy, ntl, area):
    weights = ntl * area
    assert (weights >= 0).all() and weights.sum() > 0
    return (float(np.average(cx, weights=weights)),
            float(np.average(cy, weights=weights)))


def brightest_center(cx, cy, ntl):
    k = int(np.argmax(ntl))
    return float(cx[k]), float(cy[k])


def fit(cx, cy, ntl, area, center):
    n = len(ntl)
    gamma, r2 = compute_urban_density_gradient(
        ntl, xy_distance_km(cx, cy, center),
        area, np.ones(n, dtype=bool),
    )
    if not np.isfinite(gamma) or not np.isfinite(r2):
        raise ValueError("G05 WLS gradient undefined in controlled sample")
    if r2 < -1e-10 or r2 > 1 + 1e-10:
        raise AssertionError("G05 R2 outside [0,1]")
    return float(gamma), float(r2)


def reconstruct_center(cx, cy, distances_km, *, tolerance_m=3.0):
    """Recover a rounded-distance center from archived production cell results.

    d_i^2 = (x_i - u)^2 + (y_i - v)^2, fit (u,v) using linearized
    multilateration. This recovers the NTL-selected *historical output*
    without rerunning LISA, A03 or a fresh VIIRS extraction.
    """
    good = np.isfinite(cx) & np.isfinite(cy) & np.isfinite(distances_km)
    if np.sum(good) < 20:
        raise ValueError("Need at least 20 archived center-distance observations")
    x = cx[good].astype(float)
    y = cy[good].astype(float)
    d = distances_km[good].astype(float) * 1000.0
    if np.any(d < 0):
        raise ValueError("Negative distance-to-center archive value")
    ox = float(x.mean())
    oy = float(y.mean())
    xx, yy = x - ox, y - oy
    rhs = xx*xx + yy*yy - d*d
    design = np.column_stack([2.0*xx, 2.0*yy, np.ones(len(xx))])
    coef, _, rank, _ = np.linalg.lstsq(design, rhs, rcond=None)
    if rank != 3:
        raise ValueError("Archived geometry does not identify a unique center")
    point = (float(ox + coef[0]), float(oy + coef[1]))
    error_m = np.abs(xy_distance_km(x, y, point)*1000.0 - d)
    result = {
        "n_archived_distances": int(len(d)),
        "median_abs_distance_reconstruction_m": fround(np.median(error_m)),
        "p99_abs_distance_reconstruction_m": fround(np.quantile(error_m, 0.99)),
        "max_abs_distance_reconstruction_m": fround(error_m.max()),
        "tolerance_m": tolerance_m,
        "archived_distance_rounding_km": 0.001,
    }
    if np.quantile(error_m, 0.99) > tolerance_m:
        raise ValueError("Could not reconstruct NTL-selected center from archive")
    return point, result


def synthetic_geometry():
    iy, ix = np.mgrid[0:SIDE, 0:SIDE]
    grid_id = np.arange(SIDE*SIDE, dtype=int)
    cx = 500000 + (ix.ravel() + 0.5)*CELL_M
    cy = 2000000 + (iy.ravel() + 0.5)*CELL_M
    true = (float(500000 + (TRUE_IJ[0]+0.5)*CELL_M),
            float(2000000 + (TRUE_IJ[1]+0.5)*CELL_M))
    artifact = (float(500000 + (ARTIFACT_IJ[0]+0.5)*CELL_M),
                float(2000000 + (ARTIFACT_IJ[1]+0.5)*CELL_M))
    return {"grid_id": grid_id, "cx": cx.astype(float),
            "cy": cy.astype(float), "ix": ix.ravel(),
            "iy": iy.ravel(), "area": np.full(len(grid_id), 0.25),
            "true": true, "artifact": artifact}


def synthetic_ntl(geom, replicate, amplitude):
    # Fixed generator center was selected without inspecting the NTL response.
    rng = np.random.default_rng(SEED + 17 * replicate)
    d0 = xy_distance_km(geom["cx"], geom["cy"], geom["true"])
    logmean = 3.70 - 0.37*d0
    baseline = np.maximum(0.01, np.expm1(logmean + rng.normal(0,0.28,len(d0))))
    bump_d = xy_distance_km(geom["cx"],geom["cy"],geom["artifact"])
    bump = amplitude * np.exp(-0.5 * (bump_d/ARTIFACT_SCALE_KM)**2)
    return baseline + bump


def synthetic_source(geom):
    fields = {label: synthetic_ntl(geom,0,amp)
              for label,amp in SCENARIOS.items()}
    archived = OUT / "synthetic_input.csv"
    if archived.is_file():
        src = pd.read_csv(archived, float_precision="round_trip")
        if len(src) != len(geom["cx"]):
            raise ValueError("G05 archived synthetic cell count changed")
        for k in ("grid_id", "ix", "iy"):
            if not np.array_equal(src[k].to_numpy(), geom[k]):
                raise ValueError("G05 synthetic geometry IDs differ")
        for k in ("cx", "cy", "area"):
            if not np.allclose(src[k].to_numpy(float), geom[k], atol=1e-10, rtol=0):
                raise ValueError("G05 synthetic geometry changed")
        for label, arr in fields.items():
            vals = src[label].to_numpy(float)
            if not np.allclose(vals,arr,atol=1e-10,rtol=0):
                raise ValueError("G05 generated NTL differs from source: "+label)
            fields[label] = vals
    rows = []
    for i in range(len(geom["cx"])):
        rows.append({
            "grid_id": int(geom["grid_id"][i]),
            "ix": int(geom["ix"][i]), "iy": int(geom["iy"][i]),
            "cx": number(geom["cx"][i]),
            "cy": number(geom["cy"][i]),
            "area": number(geom["area"][i]),
            **{label: number(vals[i]) for label, vals in fields.items()},
        })
    return fields, csv_text(rows, list(rows[0]))


def archived_baoan():
    if not BAOAN.is_file():
        raise FileNotFoundError("G05 requires archived Bao'an A02 CSV, not a new extraction")
    binary = BAOAN.read_bytes()
    df = pd.read_csv(io.BytesIO(binary), low_memory=False,
                     float_precision="round_trip")
    if len(df) != 7148 or not df["grid_id"].is_unique:
        raise ValueError("G05 Bao'an join key/count differs from archived A02")
    core = pd.to_numeric(df["is_border_cell"],errors="raise").to_numpy(int) == 0
    if (df["dq_status"].astype(str)!="observed").any():
        raise ValueError("G05 Bao'an A02 observation status changed")
    xcol = [x for x in df if x.startswith("centroid_x_epsg")]
    if len(xcol)!=1:
        raise ValueError("Exactly one projected x coordinate expected")
    ycol = xcol[0].replace("centroid_x_epsg","centroid_y_epsg")
    required = ("ntl_mean", "area_km2","dist_to_core_km",ycol)
    if any(col not in df.columns for col in required):
        raise ValueError("Missing archived NTL / size / distance / y columns")
    cx = df[xcol[0]].to_numpy(float)
    cy = df[ycol].to_numpy(float)
    ntl = df["ntl_mean"].to_numpy(float)
    area = df["area_km2"].to_numpy(float)
    dist_arch = df["dist_to_core_km"].to_numpy(float)
    good = np.isfinite(cx)&np.isfinite(cy)&np.isfinite(ntl)&(
        ntl >= 0)&np.isfinite(area)&(area>0)&np.isfinite(dist_arch)
    if not good[core].all():
        raise ValueError("Invalid core Bao'an observation or legacy distance")
    if core.sum()!=6186:
        raise ValueError("G05 expected 6186 full core cells from G04 provenance")
    ids=np.flatnonzero(core)
    main = {"cx":cx[ids], "cy":cy[ids],
            "ntl":ntl[ids], "area":area[ids],
            "dist_arch":dist_arch[ids], "grid_ids":df["grid_id"].to_numpy(),
            "core_idx":ids, "full_n":len(df),
            "noncore_invalid":int(np.sum(~good & ~core)),
            "core_mask":core}
    provenance = {
        "source_path":str(BAOAN.relative_to(ROOT)),
        "source_sha256":hashlib.sha256(binary).hexdigest(),
        "n_source_cells":len(df),"n_fit_core_cells":int(core.sum()),
        "n_edge_cells_not_fitted":int((~core).sum()),
        "n_noncore_rows_with_invalid_inputs":int(np.sum(~good & ~core)),
        "source_crs_columns":[xcol[0],ycol],
        "n_a02_observed":int((df["dq_status"]=="observed").sum()),
        "legacy_dist_precision_km":0.001,
    }
    return main, provenance


def evaluate_centers(source, scenario, cx, cy, ntl, area,
                     centers, reference, selected_rule="", n_clusters=None):
    r_gamma, r_r2 = fit(cx,cy,ntl,area,centers[reference])
    rows=[]
    for method, center in centers.items():
        g,r = fit(cx,cy,ntl,area,center)
        rows.append({
            "source":source,"scenario":scenario,"center_method":method,
            "center_x_epsg_m":number(center[0]),
            "center_y_epsg_m":number(center[1]),
            "center_distance_to_reference_km":fround(
                center_distance_km(center,centers[reference])),
            "reference":reference,
            "gradient_gamma_per_km":fround(g,9),
            "gradient_r2":fround(r,9),
            "delta_gamma_vs_reference":fround(g-r_gamma,9),
            "delta_r2_vs_reference":fround(r-r_r2,9),
            "n_cells_in_fit":len(ntl),
            "selection_rule":selected_rule if method in (
                "production_lisa_selected","archived_ntl_selected") else "",
            "hh_clusters_eligible":n_clusters if method in (
                "production_lisa_selected","archived_ntl_selected") else "",
        })
    return rows


def simulate_many(geom):
    """Monte Carlo on fast center heuristics only; no claim about HH algorithm."""
    results=[]
    center_true=geom["true"]
    center_geom=geometry_center(geom["cx"],geom["cy"],geom["area"])
    for rep in range(REPS):
        for scenario,amplitude in SCENARIOS.items():
            ntl=synthetic_ntl(geom, rep+1, amplitude)
            cx,cy,area=geom["cx"],geom["cy"],geom["area"]
            centers={
                "known_generator_center":center_true,
                "geometry_only_centroid":center_geom,
                "ntl_weighted_centroid":mass_center(cx,cy,ntl,area),
                "brightest_ntl_cell":brightest_center(cx,cy,ntl),
            }
            oracle_g,oracle_r2=fit(cx,cy,ntl,area,center_true)
            for method in MC_METHODS:
                c=centers[method]
                g,r2=fit(cx,cy,ntl,area,c)
                results.append({
                    "replicate":rep,
                    "scenario":scenario,"center_method":method,
                    "distance_to_known_center_km":fround(
                        center_distance_km(c,center_true),8),
                    "gradient_gamma_per_km":fround(g,9),
                    "gradient_r2":fround(r2,9),
                    "delta_gamma_vs_oracle":fround(g-oracle_g,9),
                    "delta_r2_vs_oracle":fround(r2-oracle_r2,9),
                })
    return results


def monte_carlo_summary(rows):
    res=[]
    for scenario in SCENARIOS:
        for method in MC_METHODS:
            records=[r for r in rows
                     if r["scenario"]==scenario and r["center_method"]==method]
            summary={"scenario":scenario,"center_method":method,
                     "replications":len(records)}
            for metric in ("distance_to_known_center_km",
                           "delta_gamma_vs_oracle","delta_r2_vs_oracle"):
                values=np.array([r[metric] for r in records],float)
                summary[metric]={
                    "mean":fround(np.mean(values),8),
                    "median":fround(np.median(values),8),
                    "p05":fround(np.quantile(values,0.05),8),
                    "p95":fround(np.quantile(values,0.95),8),
                    "fraction_positive":fround(np.mean(values>0),6),
                }
            res.append(summary)
    return res


def run_experiment():
    geom = synthetic_geometry()
    fields, source_csv=synthetic_source(geom)
    syn_rows=[]
    syn_cell_rows=[]
    selected=[]
    # Selected-center rule is the production function, not a surrogate maximizer
    # of regression R2; the output distance is rounded by the app to 1 meter.
    for scenario, ntl in fields.items():
        core=np.ones(len(ntl),bool)
        result=run_lisa(
            geom["cx"],geom["cy"],ntl,geom["area"],CELL_M,
            perms=PERMS,alpha=ALPHA,fdr=True,
            lit_threshold=0.0, edge_tol=0.99, min_cluster_cells=4,
            seed=SEED, weights="queen",
        )
        selected_center,reconstruction=reconstruct_center(
            geom["cx"],geom["cy"],
            result.cell_df["dist_to_core_km"].to_numpy(float),
        )
        g,r2=fit(geom["cx"],geom["cy"],ntl,geom["area"],selected_center)
        # Published regional fields are rounded; ensure our recovered center
        # actually describes the application, not a separate implementation.
        assert abs(g-result.region_metrics["urban_gradient_decay"])<0.0005
        assert abs(r2-result.region_metrics["monocentric_r2"])<0.002
        n_clusters=int(result.region_metrics["n_hh_clusters"])
        method=("largest_significant_HH_cluster_SOL_weighted"
                if n_clusters>0 else "fallback_max_half_NTL_half_neighbor_NTL")
        centers={
            "known_generator_center":geom["true"],
            "production_lisa_selected":selected_center,
            "geometry_only_centroid":geometry_center(
                geom["cx"],geom["cy"],geom["area"]),
            "ntl_weighted_centroid":mass_center(
                geom["cx"],geom["cy"],ntl,geom["area"]),
            "brightest_ntl_cell":brightest_center(
                geom["cx"],geom["cy"],ntl),
        }
        assert tuple(centers)==SYN_METHODS
        syn_rows.extend(evaluate_centers(
            "synthetic",scenario,geom["cx"],geom["cy"],
            ntl,geom["area"],centers,"known_generator_center",
            method,n_clusters
        ))
        selected.append({
            "scenario":scenario,"source":"synthetic","center_rule":method,
            "eligible_hh_clusters":n_clusters,
            "reconstruction":reconstruction,
            "selected_minus_true_center_km":fround(
                center_distance_km(selected_center,geom["true"])),
        })
        for i in range(len(ntl)):
            syn_cell_rows.append({
                "grid_id":int(geom["grid_id"][i]),"scenario":scenario,
                "ntl":number(ntl[i]),"area_km2":number(geom["area"][i]),
                "lisa_class":str(result.cell_df["lisa_class"].iloc[i]),
                "dist_true_center_km":fround(xy_distance_km(
                    geom["cx"][i],geom["cy"][i],geom["true"]),9),
                "dist_production_selected_km":fround(xy_distance_km(
                    geom["cx"][i],geom["cy"][i],selected_center),9),
                "dist_geom_center_km":fround(xy_distance_km(
                    geom["cx"][i],geom["cy"][i],centers["geometry_only_centroid"]),9),
                "dist_ntl_weighted_center_km":fround(xy_distance_km(
                    geom["cx"][i],geom["cy"][i],centers["ntl_weighted_centroid"]),9),
                "dist_brightest_cell_km":fround(xy_distance_km(
                    geom["cx"][i],geom["cy"][i],centers["brightest_ntl_cell"]),9),
            })

    # Genuine VIIRS 2020 NTL values, no independently observed economic center.
    # The production-selected NTL center is recovered from ARCHIVED rounded
    # per-cell distance, not recalculated by running LISA on existing field data.
    data, provenance = archived_baoan()
    cx,cy,ntl,area=(data[key] for key in ("cx","cy","ntl","area"))
    archived_center,reconstruct = reconstruct_center(
        cx,cy,data["dist_arch"]
    )
    real_centers={
        "archived_ntl_selected":archived_center,
        "geometry_only_centroid":geometry_center(cx,cy,area),
        "ntl_weighted_centroid":mass_center(cx,cy,ntl,area),
        "brightest_ntl_cell":brightest_center(cx,cy,ntl),
    }
    assert tuple(real_centers)==REAL_METHODS
    real_rows=evaluate_centers(
        "baoan_2020_ntl","observed_2020",cx,cy,ntl,area,real_centers,
        "archived_ntl_selected",
        selected_rule="reconstructed_from_legacy_dist_to_core_km",
    )
    full_ids=data["grid_ids"]
    row_map=np.full(data["full_n"],-1,dtype=int)
    row_map[data["core_idx"]]=np.arange(len(data["core_idx"]))
    real_cell_rows=[]
    for i in range(len(full_ids)):
        j=int(row_map[i])
        if j>=0:
            ds={method:fround(xy_distance_km(
                cx[j],cy[j],point),9) for method,point in real_centers.items()}
        else:
            ds={method:"" for method in real_centers}
        real_cell_rows.append({
            "grid_id":str(full_ids[i]),
            "is_full_core":int(j>=0),
            "ntl_used":number(ntl[j]) if j>=0 else "",
            "area_km2_used":number(area[j]) if j>=0 else "",
            "archived_rounded_center_distance_km":number(data["dist_arch"][j]) if j>=0 else "",
            **{"distance_"+method+"_km":dist for method,dist in ds.items()},
        })
    mc_rows=simulate_many(geom)
    all_comp=syn_rows+real_rows
    outputs={
        "synthetic_input.csv":source_csv,
        "synthetic_cell_results.csv":csv_text(
            syn_cell_rows,list(syn_cell_rows[0])),
        "synthetic_replications.csv":csv_text(mc_rows,MC_COLS),
        "baoan_cell_results.csv":csv_text(
            real_cell_rows,list(real_cell_rows[0])),
        "center_comparison.csv":csv_text(all_comp,COMP_COLS),
    }
    report={
        "gap":"G05",
        "status":"synthetic_known_center_and_real_NTL_center_sensitivity_only",
        "external_economic_center_verified":False,
        "economic_monocentricity_established":False,
        "identification_of_center_selection_bias_in_real_data":False,
        "app_formula_modified":False,
        "ntldata_origin":"archived_2020_VIIRS_Baoan_or_explicit_synthetic",
        "gradient_specification":"area-weighted WLS of log1p(NTL) on Euclidean distance to center, identical source function",
        "center_selection":"production run_lisa HH largest significant connected component by area, SOL-weighted center; fallback highest 0.5*(NTL+raw neighbor NTL)",
        "synthetic":{"seed":SEED,"shape":[SIDE,SIDE],"cell_size_m":CELL_M,
                     "true_generator_center_epsg_m":list(geom["true"]),
                     "artifact_location_epsg_m":list(geom["artifact"]),
                     "artifact_scale_km":ARTIFACT_SCALE_KM,
                     "scenarios":SCENARIOS,
                     "fields_replayed_from_committed_csv":True,
                     "lisa_permutations":PERMS,"fdr":True,
                     "lisa_alpha":ALPHA,"n_cells":len(geom["cx"]),
                     "synthetic_selected_center_checks":selected,
                     "monte_carlo_replications_per_scenario":REPS,
                     "repeated_center_methods":list(MC_METHODS),
                     "monte_carlo_summary":monte_carlo_summary(mc_rows),
                     "monte_carlo_scope":"fast proxy center choices only: production HH/fallback center is recomputed for the three deposited full-field synthetic scenarios, not for every MC replication",
        },
        "baoan":{**provenance,"reference":"archived_ntl_selected",
                 "reconstructed_center_epsg_m":list(archived_center),
                 "reconstruction":reconstruct,
                 "geometry_only_center_not_economic_CBD":True,
                 "center_derived_from_same_2020_NTL_as_gradient":True},
        "center_comparisons":all_comp,
        "data_counts":{"synthetic_input_cells":len(geom["cx"]),
                       "synthetic_cell_results":len(syn_cell_rows),
                       "synthetic_replications":len(mc_rows),
                       "baoan_cell_results":len(real_cell_rows),
                       "center_comparisons":len(all_comp)},
        "scientific_limits":[
            "All true-center labels are model parameters fixed before generating synthetic NTL, never observed ground truth in Bao'an.",
            "Bao'an geometric centroid is NTL-independent but not an independently identified economic CBD; no employment, POI or commuting center is supplied.",
            "The archived Bao'an NTL-selected center is reconstructed from rounded historical distance-to-center values; this does not rerun the historical LISA or A03.",
            "A higher in-sample R2 may arise from the choice of NTL-dependent reference point; neither sign nor magnitude of a true economic center-selection bias can be inferred without independent field data.",
            "Synthetic Monte Carlo only evaluates the geometric, brightness-weighted and brightest-cell proxies, not repeated production HH center inference.",
            "A single distance gradient cannot decide whether a real region is monocentric or polycentric.",
            "No live VIIRS, GHSL, A02, A03, V11, G04, G17 or G18 audit was repeated.",
        ],
        "software":{"python":sys.version.split()[0],
                    "numpy":np.__version__,"pandas":pd.__version__,
                    "scipy":scipy.__version__},
        "sha256":{"program":hashlib.sha256(
            Path(__file__).read_bytes()).hexdigest(),
            **{k:hashlib.sha256(v.encode("utf-8")).hexdigest()
               for k,v in outputs.items()}},
    }
    outputs["summary.json"] = json.dumps(report,ensure_ascii=False,indent=2,
                                         allow_nan=False)+"\n"
    return outputs


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--emit-ci",action="store_true")
    parser.add_argument("--verify",action="store_true")
    args=parser.parse_args()
    outputs=run_experiment()
    report=json.loads(outputs["summary.json"])
    assert report["data_counts"]["synthetic_cell_results"]==3*SIDE*SIDE
    assert report["data_counts"]["synthetic_replications"]==len(
        SCENARIOS)*REPS*len(MC_METHODS)
    assert report["data_counts"]["baoan_cell_results"]==7148
    print("G05_SUMMARY "+json.dumps({
        "selected":report["synthetic"]["synthetic_selected_center_checks"],
        "comparisons":report["center_comparisons"],
        "mc_summary":report["synthetic"]["monte_carlo_summary"],
        "baoan_recovery":report["baoan"]["reconstruction"],
        "rows":report["data_counts"],
    },ensure_ascii=False,sort_keys=True))
    if args.verify:
        for name,body in outputs.items():
            p=OUT/name
            if not p.is_file():
                raise SystemExit("Missing G05 evidence "+str(p))
            if p.read_text(encoding="utf-8")!=body:
                raise SystemExit("G05 evidence mismatch "+str(p))
        print("G05 exact replay passed for all six archived files")
    if args.emit_ci:
        for name,body in outputs.items():
            text=base64.b64encode(body.encode("utf-8")).decode("ascii")
            print("G05_BEGIN "+name)
            for i in range(0,len(text),4000):
                print(text[i:i+4000])
            print("G05_END "+name)


if __name__=="__main__":
    main()
