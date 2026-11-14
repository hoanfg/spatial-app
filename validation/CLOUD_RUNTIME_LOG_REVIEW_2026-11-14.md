# Streamlit Cloud runtime log review — 14 November 2026

**Source:** user-supplied Streamlit deployment log downloaded on 14 Nov 2026, containing entries from 11–14 Nov 2026 (UTC). File SHA-256: `92d1b8829288fbc50458989e4d0fcda1ec4b2486b10b77469352902d4799f873`. The full source log is retained privately, **not committed**. This report is an interpretation of the log, not an end-to-end Cloud benchmark.

## Observed facts

- Cloud startup used **Python 3.14.10** and **Streamlit 1.67.0**; package installation completed and the web server started (source lines 128–129, 245–246, 295–296).
- The dependency installation initially selected PyArrow 26.0.1, then the platform automatically replaced it with 24.0.0 because of a known segmentation-fault concern (lines 247–257). There is **no observed segmentation fault** in the log.
- Two import failures, `ModuleNotFoundError: No module named 'ntl.semantics'`, were logged on **12 November** during a GitHub code pull (lines 419–455). `Updated app!` followed at line 458, and the app was used on later dates. This historic failure is **not evidence of a current missing module**. The module is present on the reviewed `main` branch.
- 99 notices requested replacement of deprecated `st.components.v1.html` with `st.iframe`; 107 requested replacing `use_container_width` with `width`. These are deprecation notices, **not exceptions**; legacy iframe usage may originate in third-party code and needs call-site attribution before changing behavior.
- 34 warnings reported that the currently selected CartoDB tile source may require an API key. This presents a base-map availability risk, separate from numeric raster/NTL/LISA computations. An explicit tile-provider fallback should be verified visually rather than blindly swapping map style.
- 19 `Updated app!` messages appear across the captured period. Initial Git checkout processed roughly 20,023 files; that may contribute to cold startup, but this log alone does not separate Git checkout time from network and host variance.
- No explicit `MemoryError`, OOM-killer message, process termination, or execution timeout appears in this file. **Their absence does not establish an upper bound on memory or per-analysis latency.**

## Decisions and release gates

1. Carry **in-app session-accessible profiling** in the single consolidated draft PR: end-to-end and stage wall times, sampled process RSS, success/error type and JSON/CSV exports. The profiler does not claim per-user isolated memory or a physical maximum.
2. Carry A02 fail-closed six-band schema diagnostics and native-lattice GHSL quantity conservation fix in **the same PR**. They address issues found in CSV/raster comparisons; the deployment log does not directly diagnose either one.
3. Before merge, run CI and one authenticated Cloud field comparison. Confirm that VIIRS `getDownloadURL` quality-band metadata is populated or displays an explicit failure reason, and compare GHSL built/pop per-cell totals with the native-grid references. Inspect performance JSON under representative cells and cloud concurrency.
4. Treat compatibility notices as a tracked maintenance issue within review; update first-party width calls only with tested Streamlit version support, determine origin of iframe calls, and verify a no-key base-map option visually. Do not conflate cosmetic warnings with a scientific failure.

**Status:** log triage complete; production validation pending. No human user identifiers, credentials, raw log bodies, or Cloud secrets are included in this evidence report.
