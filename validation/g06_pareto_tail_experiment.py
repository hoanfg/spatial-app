#!/usr/bin/env python3
"""G06: Conditional refitted-bootstrap KS checks for NTL Pareto tails.

This is a bounded scientific audit, not a universal Pareto certificate.
Unlike the asymptotic KS p-value in the current diagnostic, the parametric
tail bootstrap re-estimates alpha in EVERY synthetic replicate. The four
top-k fractions are predeclared, not selected by KS minimization.

Important limitation: the bootstrap conditions on the observed threshold u
and number of exceedances k, assumes independent continuous Pareto draws,
and does NOT jointly bootstrap or optimize the lower cutoff. In spatially
dependent real VIIRS data, its p-value is a descriptive iid benchmark rather
than a calibrated spatial goodness-of-fit test. AICc candidate comparisons
are descriptive and do not make a candidate scientifically true.

All source provenance, software versions and evidence hashes are retained.
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
from scipy.optimize import minimize
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ntl.lisa_diagnostics import hill_diagnostics, ks_pareto  # noqa: E402

DEST = ROOT / "validation" / "evidence" / "g06_pareto_tail"
BAOAN = (ROOT / "validation" / "evidence" / "a02_post_pr27"
         / "CHN_guangdong_shenzhen_bao_an_2020_500m_lisa_cells.csv")
SEED = 6026
N_SYN = 5000
B = 399
FRACTIONS = (0.05, 0.10, 0.15, 0.20)
SOURCES = ("iid_pareto", "iid_lognormal", "iid_exponential",
           "baoan_2020_ntl")
COLUMNS = (
    "source", "tail_fraction", "n_positive", "k_tail", "u_threshold",
    "alpha_hill", "pareto_ks_D", "legacy_asymptotic_ks_p",
    "refit_bootstrap_ks_p", "refit_bootstrap_wilson95_lo",
    "refit_bootstrap_wilson95_hi", "n_bootstrap",
    "pareto_loglik", "exponential_loglik", "lognormal_loglik",
    "pareto_aicc", "exponential_aicc", "lognormal_aicc",
    "best_conditional_aicc", "aicc_exponential_minus_pareto",
    "aicc_lognormal_minus_pareto",
    "pareto_ks_D_vs_exponential_D", "pareto_ks_D_vs_lognormal_D",
    "n_threshold_ties", "n_tail_unique", "n_core",
)
B_COLUMNS = (
    "source", "tail_fraction", "replicate", "k_tail",
    "alpha_fitted_in_bootstrap", "ks_D_fitted_in_bootstrap",
    "ks_D_observed", "bootstrap_ge_observed",
)


def to_csv(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def fround(value, digits=8):
    value = float(value)
    return round(value, digits) if np.isfinite(value) else None


def wilson(success, n):
    z = 1.959963984540054
    p = success / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    half = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return [fround(max(0.0, center-half), 6),
            fround(min(1.0, center+half), 6)]


def ks_sorted(x_sorted, cdf):
    cdf = np.clip(np.asarray(cdf, float), 0.0, 1.0)
    k = x_sorted.shape[-1]
    lo = np.arange(k, dtype=float)/k
    hi = np.arange(1, k+1, dtype=float)/k
    return np.maximum(np.max(cdf-lo, axis=-1),
                      np.max(hi-cdf, axis=-1))


def conditional_pareto(x, u):
    x = np.asarray(x, float)
    if u <= 0 or np.any(x < u) or not np.isfinite(x).all():
        raise ValueError("Continuous positive tail values >= u required")
    logs = np.log(x/u)
    if logs.mean() <= 1e-12:
        raise ValueError("Degenerate Pareto tail")
    alpha = 1.0 / float(logs.mean())
    cdf = -np.expm1(-alpha * np.log(np.sort(x)/u))
    D = float(ks_sorted(np.sort(x), cdf))
    loglik = (len(x)*np.log(alpha)+len(x)*alpha*np.log(u)
              -(alpha+1)*np.log(x).sum())
    return float(alpha), D, float(loglik)


def conditional_exponential(x, u):
    excess = np.asarray(x, float) - u
    if excess.mean() <= 0:
        raise ValueError("Degenerate exponential tail")
    scale = float(excess.mean())
    cdf = -np.expm1(-np.sort(excess)/scale)
    ll = -len(x)*np.log(scale) - excess.sum()/scale
    return float(ks_sorted(np.sort(excess), cdf)), float(ll)


def conditional_lognormal(x, u, archived_parameters=None):
    # Right-tail truncated lognormal: log X ~ N(mu, sigma²) conditional X>u.
    # This is NOT the ordinary untruncated lognormal fit to the tail.
    y = np.log(np.asarray(x,float))
    lower = float(np.log(u))
    sy = float(np.std(y))
    if sy < 1e-8:
        raise ValueError("Degenerate lognormal tail")
    def minus_loglik(z):
        mu, log_sigma = float(z[0]),float(z[1])
        sd = np.exp(log_sigma)
        b=(lower-mu)/sd
        lsf=float(norm.logsf(b))
        if not np.isfinite(lsf):
            return 1e100
        value=(norm.logpdf((y-mu)/sd)-log_sigma-y-lsf).sum()
        return -float(value) if np.isfinite(value) else 1e100
    starts=((float(y.mean()),np.log(max(sy,1e-4))),
            (lower-0.5,np.log(max(sy*2,0.01))),
            (lower+0.5,np.log(max(sy,0.01))))
    candidate=[]
    for start in starts:
        z=minimize(minus_loglik,np.asarray(start),
                   method="L-BFGS-B",
                   bounds=[(lower-15.0,lower+15.0),(-4.0,3.0)],
                   options={"maxiter":160,"ftol":1e-11})
        if np.isfinite(z.fun):
            candidate.append(z)
    if not candidate:
        raise ValueError("Truncated lognormal fit did not converge")
    best=min(candidate,key=lambda a:a.fun)
    # The truncated lognormal can be nearly Pareto at the far tail:
    # its likelihood is then flat in (mu, sigma), so independent L-BFGS-B
    # runs may return slightly different but nearly equivalent optima.
    # Store a canonical rounded parameter pair and recompute rival metrics
    # from that pair. A subsequent replay uses the stored pair, but also
    # refits independently and rejects a stored pair with materially worse
    # likelihood. This is a numerical-stability policy, not extra evidence.
    if archived_parameters is None:
        mu=fround(best.x[0],8)
        sd=fround(np.exp(best.x[1]),8)
    else:
        mu=float(archived_parameters["mu_logx"])
        sd=float(archived_parameters["sigma_logx"])
    if sd <= 0 or not np.isfinite(mu+sd):
        raise ValueError("Invalid canonical truncated lognormal parameters")
    ll=-minus_loglik([mu,np.log(sd)])
    if not np.isfinite(ll) or -float(best.fun)-ll > 0.02:
        raise ValueError("Archived truncated lognormal is not near the MLE")
    yc=np.sort(y)
    log_sf_x=norm.logsf((yc-mu)/sd)
    log_sf_u=norm.logsf((lower-mu)/sd)
    cdf=-np.expm1(log_sf_x-log_sf_u)
    return (float(ks_sorted(yc,cdf)),float(ll),
            {"mu_logx":fround(mu,8),"sigma_logx":fround(sd,8),
             "converged":bool(best.success)})


def aicc(loglik, k, n):
    return float(2*k - 2*loglik + 2*k*(k+1)/(n-k-1))


def sim_source():
    rng=np.random.default_rng(SEED)
    # Exact heavy-tail control has alpha = 2.5, cutoff 1.
    pareto = 1.0 + rng.pareto(2.5,size=N_SYN)
    # Rival non-Pareto parent distributions. All have positive continuous
    # values; matching their means to NTL is NOT attempted or claimed.
    lognormal = rng.lognormal(0.5,1.15,size=N_SYN)
    exponential = 0.2 + rng.exponential(2.3,size=N_SYN)
    generated={"iid_pareto":pareto,"iid_lognormal":lognormal,
               "iid_exponential":exponential}
    p=DEST/"synthetic_input.csv"
    if p.is_file():
        df=pd.read_csv(p,float_precision="round_trip")
        if len(df)!=N_SYN or not np.array_equal(
                df["synthetic_id"].to_numpy(),np.arange(N_SYN)):
            raise ValueError("Archived G06 synthetic source ID mismatch")
        for name,values in generated.items():
            archived=df[name].to_numpy(float)
            if not np.allclose(archived,values,atol=1e-10,rtol=0):
                raise ValueError("Synthetic source deviates from seeded design: "+name)
            generated[name]=archived
    records=[{"synthetic_id":i,
              **{name:repr(float(values[i])) for name,values in generated.items()}}
             for i in range(N_SYN)]
    return generated,to_csv(records,["synthetic_id",*generated])


def load_real():
    if not BAOAN.is_file():
        raise FileNotFoundError("G06 source missing: "+str(BAOAN))
    src=BAOAN.read_bytes()
    df=pd.read_csv(io.BytesIO(src),low_memory=False,
                   float_precision="round_trip")
    if len(df)!=7148 or not df["grid_id"].is_unique:
        raise ValueError("Unexpected Bao'an CSV IDs or count")
    if not (df["dq_status"].astype(str)=="observed").all():
        raise ValueError("G06 Bao'an not all observed")
    core=pd.to_numeric(df["is_border_cell"],errors="raise").to_numpy(int)==0
    ntl=df["ntl_mean"].to_numpy(float)
    if np.any(~np.isfinite(ntl[core])) or np.any(ntl[core]<0):
        raise ValueError("Invalid core NTL values")
    if int(core.sum())!=6186:
        raise ValueError("G06 Bao'an core count changed from G04/G05")
    selected=core&(ntl>0)
    out=ntl[selected]
    if len(out)<100:
        raise ValueError("G06 has insufficient positive core data")
    records=[]
    # Full join table preserves all IDs. No "measured zero" is silently
    # made into a Pareto exceedance, and border observations remain excluded.
    positive_order=np.flatnonzero(selected)
    descending=positive_order[np.argsort(-ntl[positive_order],kind="stable")]
    ranks=np.full(len(df),-1,dtype=int)
    ranks[descending]=np.arange(1,len(descending)+1)
    for i in range(len(df)):
        records.append({
          "grid_id":str(df["grid_id"].iloc[i]),
          "is_full_core":int(core[i]),
          "included_positive_core":int(selected[i]),
          "ntl_mean_original":repr(float(ntl[i])) if np.isfinite(ntl[i]) else "",
          "positive_core_descending_rank":int(ranks[i]) if ranks[i]>0 else "",
        })
    provenance={
       "path":str(BAOAN.relative_to(ROOT)),
       "sha256":hashlib.sha256(src).hexdigest(),
       "source_rows":int(len(df)),
       "core_rows":int(core.sum()),
       "positive_core_rows":int(selected.sum()),
       "zero_core_rows":int((core&(ntl==0)).sum()),
       "border_rows":int((~core).sum()),
       "observed_a02_rows":int((df["dq_status"]=="observed").sum()),
    }
    fields=list(records[0])
    return out,provenance,to_csv(records,fields)


def conditional_refit_bootstrap(x, u, alpha, D, key):
    k=len(x)
    rng=np.random.default_rng(SEED+1000+key*104729)
    # Conditional on the observed empirical (k+1)st value u, sample k iid
    # Pareto exceedances; re-estimate alpha for EACH bootstrap replicate.
    logratios=rng.exponential(scale=1.0/alpha,size=(B,k))
    alphab=1.0/logratios.mean(axis=1)
    sortedlog=np.sort(logratios,axis=1)
    cdf=-np.expm1(-alphab[:,None]*sortedlog)
    Db=ks_sorted(sortedlog,cdf)
    hits=Db>=D-1e-12
    p=(1+int(hits.sum()))/(B+1)
    conf=wilson(int(hits.sum()),B)
    rows=[{
        "source":SOURCES[key//len(FRACTIONS)],
        "tail_fraction":FRACTIONS[key%len(FRACTIONS)],
        "replicate":b,
        "k_tail":k,
        "alpha_fitted_in_bootstrap":repr(fround(alphab[b],7)),
        "ks_D_fitted_in_bootstrap":repr(fround(Db[b],7)),
        "ks_D_observed":repr(fround(D,7)),
        "bootstrap_ge_observed":int(hits[b]),
    } for b in range(B)]
    return p,conf,rows


def calculate():
    syn,src_csv=sim_source()
    real,realmeta,real_csv=load_real()
    data={**syn,"baoan_2020_ntl":real}
    if tuple(data)!=SOURCES:
        raise AssertionError("G06 source order must remain stable")
    saved_fit={}
    summary_file=DEST/"summary.json"
    if summary_file.is_file():
        previous=json.loads(summary_file.read_text(encoding="utf-8"))
        if previous.get("gap")!="G06":
            raise ValueError("Archived G06 fit metadata source invalid")
        saved_fit={
            (item["source"],float(item["tail_fraction"])):
                item["conditional_lognormal_parameters"]
            for item in previous["fit_details"]
        }
        if len(saved_fit)!=len(SOURCES)*len(FRACTIONS):
            raise ValueError("Archived truncated lognormal parameter grid incomplete")
    cases=[]
    boots=[]
    fitmeta=[]
    for si,(name,values) in enumerate(data.items()):
        values=np.asarray(values,float)
        if np.any(values<=0) or not np.isfinite(values).all():
            raise ValueError("G06 all included values must be positive/finite")
        vals=np.sort(values)[::-1]
        n=len(vals)
        for fi,frac in enumerate(FRACTIONS):
            k=int(math.floor(frac*n))
            if k<30 or k+1>=n:
                raise ValueError("Tail size/cutoff invalid")
            u=float(vals[k])
            top=vals[:k]
            alpha,D,llp=conditional_pareto(top,u)
            legacy=hill_diagnostics(
                vals,np.ones(n,bool),np.ones(n,bool),tail_frac=frac)
            if (abs(legacy["alpha"]-alpha)>1e-9 or
                abs(legacy["ks_D"]-D)>1e-9 or int(legacy["k"])!=k):
                raise AssertionError("G06 must match production Hill and KS arithmetic")
            Dexp,llexp=conditional_exponential(top,u)
            Dlog,lllog,logparam=conditional_lognormal(
                top,u,saved_fit.get((name,float(frac))))
            p,conf,rows=conditional_refit_bootstrap(
                top,u,alpha,D,si*len(FRACTIONS)+fi)
            boots.extend(rows)
            scores={
                "pareto":aicc(llp,1,k),
                "exponential":aicc(llexp,1,k),
                "lognormal":aicc(lllog,2,k),
            }
            cases.append({
               "source":name,"tail_fraction":frac,"n_positive":n,
               "k_tail":k,"u_threshold":fround(u,9),
               "alpha_hill":fround(alpha,8),"pareto_ks_D":fround(D,8),
               "legacy_asymptotic_ks_p":fround(legacy["ks_p"],8),
               "refit_bootstrap_ks_p":fround(p,8),
               "refit_bootstrap_wilson95_lo":conf[0],
               "refit_bootstrap_wilson95_hi":conf[1],
               "n_bootstrap":B,
               "pareto_loglik":fround(llp,6),
               "exponential_loglik":fround(llexp,6),
               "lognormal_loglik":fround(lllog,6),
               "pareto_aicc":fround(scores["pareto"],6),
               "exponential_aicc":fround(scores["exponential"],6),
               "lognormal_aicc":fround(scores["lognormal"],6),
               "best_conditional_aicc":min(scores,key=scores.get),
               "aicc_exponential_minus_pareto":fround(
                   scores["exponential"]-scores["pareto"],6),
               "aicc_lognormal_minus_pareto":fround(
                   scores["lognormal"]-scores["pareto"],6),
               "pareto_ks_D_vs_exponential_D":fround(D-Dexp,8),
               "pareto_ks_D_vs_lognormal_D":fround(D-Dlog,8),
               "n_threshold_ties":int(np.sum(vals==u)),
               "n_tail_unique":int(np.unique(top).size),
               "n_core":n if si<3 else int(realmeta["core_rows"]),
            })
            fitmeta.append({
                "source":name,"tail_fraction":frac,
                "n_tail":k,"u":fround(u,9),
                "conditional_lognormal_parameters":logparam,
                "pareto_alpha":fround(alpha,8),
            })
    summaries=[]
    for name in SOURCES:
        these=[r for r in cases if r["source"]==name]
        summaries.append({
            "source":name,"estimated_alpha_range":[min(r["alpha_hill"] for r in these),
                                                   max(r["alpha_hill"] for r in these)],
            "bootstrap_p_range":[min(r["refit_bootstrap_ks_p"] for r in these),
                                 max(r["refit_bootstrap_ks_p"] for r in these)],
            "conditional_aicc_winners":[r["best_conditional_aicc"] for r in these],
            "reported_fractions":[r["tail_fraction"] for r in these],
        })
    outputs={
       "synthetic_input.csv":src_csv,
       "baoan_tail_observations.csv":real_csv,
       "tail_cases.csv":to_csv(cases,COLUMNS),
       "bootstrap_replications.csv":to_csv(boots,B_COLUMNS),
    }
    report={
        "gap":"G06",
        "status":"bounded_conditional_iid_pareto_tail_fit_checks_not_spatial_validation",
        "pareto_distribution_established_for_real_Baoan":False,
        "app_production_ks_changed":False,
        "existing_numerical_hill_ks_tests_repeated":False,
        "seed":SEED,"n_synthetic_each_distribution":N_SYN,
        "synthetic_data_generating_processes":{
            "iid_pareto":"1 + Pareto Type I excess, alpha=2.5; true lower support 1",
            "iid_lognormal":"lognormal with mu(log X)=0.5 and sigma(log X)=1.15",
            "iid_exponential":"0.2 + Exponential with scale 2.3",
        },
        "fixed_tail_fractions":list(FRACTIONS),
        "bootstrap_replicates_per_case":B,
        "bootstrap_reference":"continuous iid Pareto exceeding the observed order-statistic cutoff u, conditioned on observed u and k",
        "bootstrap_parameter_reestimation":"alpha fitted separately in each bootstrap sample",
        "bootstrap_p_definition":"(1 + number of refit KS values >= observed KS)/(B+1)",
        "bootstrap_cutoff_reestimated":False,
        "cutoff_method":"predeclared top-k fractions; threshold is the (k+1)st largest positive NTL, matching production Hill convention",
        "rival_comparison":"same k and same u; conditional tail Pareto, shifted exponential and left-truncated lognormal, fitted separately with AICc",
        "aicc_not_an_absolute_goodness_of_fit_test":True,
        "real_input":realmeta,
        "scenario_count":len(cases),
        "bootstrap_row_count":len(boots),
        "fit_details":fitmeta,
        "source_summaries":summaries,
        "scientific_limits":[
          "The bootstrap models continuous independent excesses; spatial and temporal VIIRS dependence invalidates unconditional field p-value interpretation.",
          "The empirical threshold u and count k are conditioned on, not selected and reestimated in bootstrap; this is not the full Clauset-Shalizi-Newman cutoff-selection procedure.",
          "The tail fractions are predeclared sensitivity cases and cannot be data-mined for a favorable p-value without multiple-comparison adjustment.",
          "The fitted lognormal is correctly conditioned on exceeding u, unlike fitting an ordinary lognormal directly to the upper tail.",
          "AICc differences compare fitted conditional densities on exactly the same exceedances, but a lowest AICc is not proof any candidate is true.",
          "Sample ties/rounding and VIIRS zero clipping may change empirical KS and alter interpretation; included core values are explicitly recorded.",
          "Failure to reject a Pareto conditional iid reference cannot establish a Pareto law or economic mechanism.",
          "Known Pareto, lognormal and exponential controls are entirely generated; no external NTL source is implied.",
          "No original A02/A03/A04/V11, GHSL, G04, G05, G17 or G18 evidence is modified or rerun.",
        ],
        "method_reference":"Clauset, Shalizi and Newman (2009), DOI:10.1137/070710111",
        "software":{"python":sys.version.split()[0],
                    "numpy":np.__version__,"pandas":pd.__version__,
                    "scipy":scipy.__version__},
        "sha256":{
            "generator_py":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            **{name:hashlib.sha256(body.encode("utf-8")).hexdigest()
               for name,body in outputs.items()},
        },
        "cases":cases,
    }
    outputs["summary.json"]=json.dumps(report,ensure_ascii=False,indent=2,
                                         allow_nan=False)+"\n"
    return outputs


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    p.add_argument("--emit-ci",action="store_true")
    p.add_argument("--emit-ci-updates",action="store_true")
    args=p.parse_args()
    outputs=calculate()
    report=json.loads(outputs["summary.json"])
    assert report["scenario_count"]==len(SOURCES)*len(FRACTIONS)
    assert report["bootstrap_row_count"]==len(SOURCES)*len(FRACTIONS)*B
    assert report["real_input"]["source_rows"]==7148
    print("G06_SUMMARY "+json.dumps({
        "sources":report["source_summaries"],
        "real_input":report["real_input"],
        "cases":report["cases"],
        "bootstrap_rows":report["bootstrap_row_count"],
        "replay":args.verify,
    },ensure_ascii=False,sort_keys=True))
    if args.verify:
        for name,body in outputs.items():
            path=DEST/name
            if not path.is_file():
                raise SystemExit("Missing archived G06 evidence: "+str(path))
            if path.read_text(encoding="utf-8")!=body:
                raise SystemExit("G06 evidence mismatch: "+str(path))
        print("G06 exact evidence replay succeeded")
    if args.emit_ci or args.emit_ci_updates:
        for name,body in outputs.items():
            if args.emit_ci_updates and name not in (
                    "tail_cases.csv", "bootstrap_replications.csv", "summary.json"):
                continue
            encoded=base64.b64encode(body.encode("utf-8")).decode("ascii")
            print("G06_BEGIN "+name)
            for j in range(0,len(encoded),4000):
                print(encoded[j:j+4000])
            print("G06_END "+name)


if __name__=="__main__":
    main()
