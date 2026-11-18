#!/usr/bin/env python3
"""G04 evidence: NTL-distance-potential construct stress and real-data sensitivity.

This is NOT a validation of economic market access or causal recentering.
Existing T07 has already tested the mathematical permutation expectation.
No VIIRS/GHSL extraction or A02/A03/A04/V11 validations are repeated.

Evidence:
  synthetic_input.csv: predetermined synthetic geometry, job mass, light proxies
  synthetic_cell_results.csv: every synthetic cell under baseline kernel
  baoan_cell_results.csv: every Bao'an cell, joined to existing archived source
  sensitivity.csv: all tau/radius and proxy specifications
  summary.json: provenance, limitations, checksums and summary

Run in root: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
    python validation/g04_ntl_potential_experiment.py --verify
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ntl.lisa_core import compute_recentered_market_access  # noqa: E402

OUT = ROOT / "validation" / "evidence" / "g04_ntl_potential"
BAOAN = ROOT / "validation" / "evidence" / "a02_post_pr27" / "CHN_guangdong_shenzhen_bao_an_2020_500m_lisa_cells.csv"
SEED = 4026
CELL_M = 500.0
SETTINGS = tuple((radius, tau) for radius in (3, 5, 8) for tau in (0.25, 0.5, 1.0))
BASE = (5, 0.5)
SCENARIOS = ("light_aligned", "bright_nonjob_artifact", "shuffled_placebo")
SENS_COLS = ("source", "scenario", "radius_steps", "tau_per_km", "n_core",
             "reference", "rank_corr_vs_independent_jobs", "rank_corr_vs_baseline",
             "top_decile_jaccard_vs_baseline", "rank_corr_raw_vs_centered",
             "rank_corr_raw_vs_kernel_exposure", "rank_corr_centered_vs_kernel_exposure",
             "share_centered_negative", "mean_raw", "mean_expected", "mean_centered",
             "std_centered")


def csv_text(rows, fields):
    f = io.StringIO(newline="")
    writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return f.getvalue()


def rfloat(x, digits=8):
    x = float(x)
    return round(x, digits) if np.isfinite(x) else None


def rank_r(x, y):
    mask = np.isfinite(x) & np.isfinite(y)
    if np.sum(mask) < 5:
        return None
    if np.std(x[mask]) < 1e-12 or np.std(y[mask]) < 1e-12:
        return None
    return rfloat(spearmanr(x[mask], y[mask]).statistic)


def top_decile_jaccard(x, y):
    mask = np.isfinite(x) & np.isfinite(y)
    n = int(mask.sum())
    if n < 10:
        return None
    ids = np.flatnonzero(mask)
    k = max(1, int(np.ceil(0.10 * n)))
    a = set(ids[np.argsort(-x[ids], kind="stable")[:k]].tolist())
    b = set(ids[np.argsort(-y[ids], kind="stable")[:k]].tolist())
    return rfloat(len(a & b) / len(a | b))


def gaussian(x, y, cx, cy, width):
    return np.exp(-((x-cx)**2+(y-cy)**2)/(2.0*width**2))


def generated_synthetic():
    rng = np.random.default_rng(SEED)
    iy, ix = np.mgrid[0:25, 0:25]
    x = ix.ravel().astype(float)-12.0
    y = iy.ravel().astype(float)-12.0
    keep = ((x/11.5)**2+(y/10.0)**2 <= 1.0)
    keep &= ~((x>=4)&(x<=7)&(y>=2)&(y<=4))  # an irregular inland exclusion
    keep &= ~((x<=-6)&(y<=-5))
    x, y = x[keep], y[keep]
    cx, cy = 500000.0+(x+12.5)*CELL_M, 2000000.0+(y+12.5)*CELL_M
    jobs = 1.5+rng.gamma(1.8,2.4,len(x))
    jobs += 55.0*gaussian(x,y,-3,1,2.7)+37.0*gaussian(x,y,4,-2,2.3)
    # Known synthetic "jobs": generated first, not fitted from simulated NTL.
    # The aligned NTL shares latent jobs by explicit construction; this is
    # intentionally not an independent field observation.
    light = 0.58*jobs + rng.gamma(2.0,2.0,len(x))
    light = np.clip(light,0.001,None)
    art = light + 145.0*gaussian(x,y,7,6,1.2)
    placebo = rng.permutation(light)
    fields = dict(
        grid_id=np.arange(len(x),dtype=int),
        cx=cx, cy=cy,
        area=np.full(len(x),0.25),
        jobs_mass=jobs*0.25,
        light_aligned=light,
        bright_nonjob_artifact=art,
        shuffled_placebo=placebo,
    )
    assert len(fields["cx"]) > 250
    return fields


def load_synthetic():
    fields = generated_synthetic()
    archived = OUT / "synthetic_input.csv"
    if archived.is_file():
        source = pd.read_csv(archived, dtype={"grid_id":int}, float_precision="round_trip")
        if len(source) != len(fields["cx"]):
            raise ValueError("G04 synthetic source cell count mismatch")
        if not np.array_equal(source["grid_id"].to_numpy(), fields["grid_id"]):
            raise ValueError("G04 synthetic source IDs changed")
        for key in ("cx", "cy", "area", "jobs_mass", *SCENARIOS):
            vals = source[key].to_numpy(float)
            if not np.allclose(vals, fields[key], rtol=0.0, atol=1e-9):
                raise ValueError("G04 synthetic source deviates from seeded design: "+key)
            fields[key] = vals
    rows=[]
    for i in range(len(fields["cx"])):
        row={}
        for key in ("grid_id","cx","cy","area","jobs_mass",*SCENARIOS):
            row[key]=int(fields[key][i]) if key=="grid_id" else repr(float(fields[key][i]))
        rows.append(row)
    return fields, csv_text(rows,list(rows[0]))


def load_baoan():
    if not BAOAN.is_file():
        raise FileNotFoundError("Deposited Bao'an A02 post-PR27 source missing: "+str(BAOAN))
    file_bytes=BAOAN.read_bytes()
    df=pd.read_csv(io.BytesIO(file_bytes),low_memory=False)
    if len(df)!=7148 or not df["grid_id"].is_unique:
        raise ValueError("Expected 7148 unique Bao'an cells")
    xcols=[c for c in df if c.startswith("centroid_x_epsg")]
    if len(xcols)!=1:
        raise ValueError("Bao'an requires exactly one projected x coordinate: "+str(xcols))
    xcol=xcols[0]; ycol=xcol.replace("centroid_x_epsg","centroid_y_epsg")
    if ycol not in df.columns:
        raise ValueError("Bao'an matching projected y coordinate missing")
    required=("grid_id","ntl_mean","area_km2","is_border_cell","dq_status")
    if any(c not in df.columns for c in required):
        raise ValueError("Bao'an input missing columns: "+str(set(required)-set(df.columns)))
    if not (df["dq_status"].astype(str)=="observed").all():
        raise ValueError("Bao'an case differs from archived all-observed A02 status")
    ntl=df["ntl_mean"].to_numpy(float)
    area=df["area_km2"].to_numpy(float)
    x,y=df[xcol].to_numpy(float),df[ycol].to_numpy(float)
    good=np.isfinite(x)&np.isfinite(y)&np.isfinite(ntl)&np.isfinite(area)&(ntl>=0)&(area>0)
    if not good.all():
        raise ValueError("Bao'an source includes invalid projected, NTL or area fields")
    border=pd.to_numeric(df["is_border_cell"],errors="raise").to_numpy(dtype=int)
    if not np.isin(border,[0,1]).all():
        raise ValueError("Bao'an border flags must be binary")
    core=(border==0)
    if core.sum()<10:
        raise ValueError("Bao'an has too few full core cells")
    data={"grid_id":df["grid_id"].to_numpy(), "cx":x, "cy":y,
          "area":area, "ntl":ntl, "sol":ntl*area, "core":core}
    source={"path":str(BAOAN.relative_to(ROOT)),
            "sha256":hashlib.sha256(file_bytes).hexdigest(),
            "n_source_cells":len(df), "n_core":int(core.sum()),
            "n_border_excluded":int((~core).sum()),
            "coordinate_x":xcol,"coordinate_y":ycol,
            "support_observed":int((df["dq_status"]=="observed").sum())}
    return data,source


def metrics(source, scenario, radius, tau, rec, raw, expected, core, base_rec,
            benchmark=None):
    ids=np.flatnonzero(core)
    all_finite=np.isfinite(raw[ids])&np.isfinite(expected[ids])&np.isfinite(rec[ids])
    if not all_finite.all():
        raise ValueError("G04 active core contains nonfinite output")
    denominator=np.mean(expected[ids]/np.maximum(1e-12,1.0))
    # Expected exposure is the geometry-only weight sum times core mean SOL.
    out={
        "source":source,"scenario":scenario,"radius_steps":radius,
        "tau_per_km":tau,"n_core":len(ids),
        "reference":"synthetic_jobs_distance_potential" if benchmark is not None else "none_real_proxy_missing",
        "rank_corr_vs_independent_jobs":rank_r(rec[ids],benchmark[ids]) if benchmark is not None else None,
        "rank_corr_vs_baseline":rank_r(rec[ids],base_rec[ids]),
        "top_decile_jaccard_vs_baseline":top_decile_jaccard(rec[ids],base_rec[ids]),
        "rank_corr_raw_vs_centered":rank_r(raw[ids],rec[ids]),
        "rank_corr_raw_vs_kernel_exposure":rank_r(raw[ids],expected[ids]),
        "rank_corr_centered_vs_kernel_exposure":rank_r(rec[ids],expected[ids]),
        "share_centered_negative":rfloat(np.mean(rec[ids]<0)),
        "mean_raw":rfloat(np.mean(raw[ids])),
        "mean_expected":rfloat(np.mean(expected[ids])),
        "mean_centered":rfloat(np.mean(rec[ids])),
        "std_centered":rfloat(np.std(rec[ids],ddof=1)),
    }
    return out


def calc(cx,cy,sol,core,radius,tau):
    return compute_recentered_market_access(
        cx,cy,sol,core,CELL_M,radius_steps=radius,tau_km=tau
    )


def run_experiment():
    syn,source_csv=load_synthetic()
    real,real_provenance=load_baoan()
    results=[]
    cells=[]
    synthetic_base={}
    # This is a constructed "jobs accessibility" reference, not employment data.
    synthetic_jobs_oracle=calc(syn["cx"],syn["cy"],syn["jobs_mass"],
                               np.ones(len(syn["cx"]),dtype=bool),*BASE)[0]
    for scenario in SCENARIOS:
        core=np.ones(len(syn["cx"]),dtype=bool)
        sol=syn[scenario]*syn["area"]
        baseline=calc(syn["cx"],syn["cy"],sol,core,*BASE)
        synthetic_base[scenario]=baseline
        for radius,tau in SETTINGS:
            raw,expected,rec=calc(syn["cx"],syn["cy"],sol,core,radius,tau)
            results.append(metrics("synthetic",scenario,radius,tau,
                                   rec,raw,expected,core,baseline[2],
                                   synthetic_jobs_oracle))
        raw,expected,rec=baseline
        for i in range(len(syn["cx"])):
            cells.append({
                "grid_id":int(syn["grid_id"][i]),
                "scenario":scenario,
                "known_jobs_access":repr(float(synthetic_jobs_oracle[i])),
                "ntl_raw_access":repr(float(raw[i])),
                "ntl_expected_permutation":repr(float(expected[i])),
                "ntl_centered_access":repr(float(rec[i]))
            })

    core=real["core"]
    base_real=calc(real["cx"],real["cy"],real["sol"],core,*BASE)
    for radius,tau in SETTINGS:
        raw,expected,rec=calc(real["cx"],real["cy"],real["sol"],core,radius,tau)
        results.append(metrics("baoan_real_ntl","observed_2020",radius,tau,
                               rec,raw,expected,core,base_real[2]))
    real_rows=[]
    for i in range(len(core)):
        raw,expected,rec=(component[i] for component in base_real)
        real_rows.append({
            "grid_id":str(real["grid_id"][i]),
            "is_full_cell":int(core[i]),
            "ntl_raw_access":"" if not np.isfinite(raw) else repr(float(raw)),
            "ntl_expected_permutation":"" if not np.isfinite(expected) else repr(float(expected)),
            "ntl_centered_access":"" if not np.isfinite(rec) else repr(float(rec)),
        })
    sensitivity_csv=csv_text(results,SENS_COLS)
    synthetic_cell_csv=csv_text(cells,list(cells[0]))
    real_cell_csv=csv_text(real_rows,list(real_rows[0]))
    report={
        "gap":"G04",
        "status":"synthetic_construct_stress_and_observed_NTL_sensitivity_only",
        "economic_construct_validation":False,
        "causal_identification":False,
        "completed_numerical_identity_T07_rerun":False,
        "synthetic_seed":SEED,
        "cell_size_m":CELL_M,
        "baseline":{"radius_steps":BASE[0],"tau_per_km":BASE[1],
                    "support_radius_km":BASE[0]*CELL_M/1000,
                    "exponential_half_distance_km":round(math.log(2)/BASE[1],6)},
        "settings":[{"radius_steps":r,"tau_per_km":t,
                    "max_distance_km":r*CELL_M/1000} for r,t in SETTINGS],
        "source_baoan":real_provenance,
        "synthetic":{"cells":len(syn["cx"]),"known_jobs_only_generated":True,
            "scenario_definitions":{
              "light_aligned":"0.58*jobs_density + independent positive gamma measurement",
              "bright_nonjob_artifact":"aligned light plus nonjob hotspot centered (7,6)",
              "shuffled_placebo":"single seeded permutation of aligned NTL across fixed cells"
            },
            "oracle_definition":"distance weighted mass of synthetic jobs, at baseline tau=0.5 and radius=5",
            "oracle_independence_caution":"The known synthetic jobs are generated first, but aligned NTL is explicitly generated from them; this is an engineered mechanism, not independent external employment measurement."
        },
        "sensitivity_rows":len(results),
        "synthetic_cell_output_rows":len(cells),
        "baoan_cell_output_rows":len(real_rows),
        "software":{"python":sys.version.split()[0],
                    "numpy":np.__version__,"pandas":pd.__version__,"scipy":scipy.__version__},
        "metric_definitions":{
            "rank_corr_vs_independent_jobs":"Spearman centered NTL potential against controlled synthetic jobs distance potential (null for observed Bao'an)",
            "rank_corr_vs_baseline":"Spearman of centered variants against baseline centered potential on same analyzed cells",
            "top_decile_jaccard_vs_baseline":"overlap of top ceil(10%*n) ranked core cells",
            "rank_corr_raw_vs_kernel_exposure":"Spearman raw weighted SOL and location-only permutation expectation; NOT exogeneity",
            "rank_corr_centered_vs_kernel_exposure":"Spearman centered weighted SOL and location-only permutation expectation; NOT evidence of causal independence",
            "share_centered_negative":"fraction of eligible cells whose recentered potential is below the permutation mean",
        },
        "limitations":[
            "No matched independent population, employment, market size, travel cost or transport network exists in this deposited Bao'an source.",
            "Synthetic jobs are known by construction; aligned NTL is generated from jobs and is not independent field validation.",
            "A single shuffled negative-control NTL field is descriptive, not a permutation p-value or significance test.",
            "Centering subtracts expectation under exchangeable spatial assignments, not conditional expectation under an identified exogenous economic shock.",
            "The real sample retains the original 2020 Bao'an 500m radiance, area and projected coordinates. Border cells are output with blank access and excluded from all comparable core-cell summaries.",
            "Tau is a fixed hypothetical exponential kernel parameter in inverse kilometers, not estimated commuting friction or travel cost.",
            "The influence of radius, tau and bright nonjob activity cannot be read as identified market effects.",
            "This experiment does not rerun V11, GHSL, A02, A03, A04, G17, G18, or the T07 permutation expectation theorem.",
        ],
        "sensitivity":results,
    }
    outputs={
        "synthetic_input.csv":source_csv,
        "synthetic_cell_results.csv":synthetic_cell_csv,
        "baoan_cell_results.csv":real_cell_csv,
        "sensitivity.csv":sensitivity_csv,
    }
    report["sha256"]={
        "generator_py":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **{k:hashlib.sha256(v.encode("utf-8")).hexdigest() for k,v in outputs.items()}
    }
    outputs["summary.json"]=json.dumps(report,ensure_ascii=False,
                                        allow_nan=False,indent=2)+"\n"
    return outputs


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--emit-ci",action="store_true")
    parser.add_argument("--verify",action="store_true")
    args=parser.parse_args()
    outputs=run_experiment()
    report=json.loads(outputs["summary.json"])
    assert report["sensitivity_rows"]==len(SCENARIOS)*len(SETTINGS)+len(SETTINGS)
    assert report["source_baoan"]["n_source_cells"]==7148
    important={
       "source_baoan":report["source_baoan"],
       "n_synthetic":report["synthetic"]["cells"],
       "baseline":report["baseline"],
       "baseline_syn":[r for r in report["sensitivity"]
                       if r["source"]=="synthetic" and
                       r["radius_steps"]==BASE[0] and r["tau_per_km"]==BASE[1]],
       "real_variants":[r for r in report["sensitivity"]
                        if r["source"]=="baoan_real_ntl"],
    }
    print("G04_SUMMARY "+json.dumps(important,ensure_ascii=False,sort_keys=True))
    if args.verify:
        for name,body in outputs.items():
            target=OUT/name
            if not target.is_file():
                raise SystemExit("Missing G04 evidence: "+str(target))
            if target.read_text(encoding="utf-8")!=body:
                raise SystemExit("G04 evidence mismatch: "+str(target))
        print("G04 evidence replay matches all five archived files")
    if args.emit_ci:
        for name,body in outputs.items():
            b64=base64.b64encode(body.encode("utf-8")).decode("ascii")
            print("G04_BEGIN "+name)
            for i in range(0,len(b64),4000):
                print(b64[i:i+4000])
            print("G04_END "+name)


if __name__=="__main__":
    main()
