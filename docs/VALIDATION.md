# Validation record

Date: 2026-09-30.

## Checks completed in this build

- 19 Python unittest methods passed, including 12 multilingual fixture cases inside a parameterized test. See [raw test output](results/unittest.txt).
- Local HTTP round-trip analysis, asset serving, generation-disabled handling, request-token checks, cross-origin rejection and path traversal checks passed.
- Python modules compiled and the frontend JavaScript passed `node --check` syntax validation.
- A distributable Python wheel built successfully with setuptools. The wheel contains the web assets and fixture JSON.
- A warm CPU timing run covered 360 analyses, with five warm-ups and 30 repetitions per synthetic case. See [machine-readable results](results/cpu-fixture-benchmark.json). This was an x86_64 Linux environment, not a Snapdragon HP PC.
- A mixed Telugu sample produced the [example JSON report](results/example-report.json).

## Not established

- Browser visual/interactivity validation could not be completed: the local browser binary was unavailable and its download failed. HTTP API and static asset checks passed, but they do not establish full browser compatibility.
- Windows or Windows ARM64 installation was not tested locally. The included CI workflow requests Windows and Linux jobs after publication; those jobs have not yet run.
- Real E5 weights, a real local LLM server and native-speaker cultural evidence were not available for validation.
- No Snapdragon NPU execution, CPU/NPU comparison, power measurement, peak memory figure or general cultural accuracy is reported.

The very small synthetic pack makes the CPU timing run cheap. These timings must not be presented as the latency of the proposed full neural pipeline or extrapolated to a large corpus.
