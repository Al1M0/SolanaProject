# Verified reproduction runtime

Use **Python 3.12** for the current frozen-engine bundles and the submission demonstration. No third-party Python packages or provider requests are needed:

```bash
python3.12 --version
python3.12 reproduce.py
```

The committed reference was verified on Python 3.12.14. The actual fresh browser export shown in the demo was verified on Python 3.12.15 with exact checksums and result fingerprints. These are measured checks, not a guarantee across every Python release or platform.

## Compatibility defect discovered in review

Older export instructions advertise “Python 3.10+”. That is too broad for **exact floating-point result hashes**. The first fresh browser archive failed on Python 3.11.6. Recursive comparison found 1,018 unequal numeric leaves, no type-only differences and no nonnumeric differences. The largest absolute numerical difference was about 1.82×10⁻¹². The same unchanged archive then passed on Python 3.12.15.

Python's [official 3.12 documentation](https://docs.python.org/3.12/library/functions.html#sum) records a changed float-summation algorithm. The engine uses float `sum()`; the observed version difference is consistent with that documented change. No tolerance, rounding, result rewriting, benchmark change or parameter tuning was used to obtain a passing run.

Frozen engine/source bytes and existing bundles are retained. This note corrects the submission's runtime instructions. The running application's older generated “3.10+” description has not been redeployed in this media/documentation pass. A future engine release should record runtime provenance in new manifests and enforce supported runtimes with a readable error, while retaining historical snapshots. Exact portability beyond the tested runtimes remains unverified.
