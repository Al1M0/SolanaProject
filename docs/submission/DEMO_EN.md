# English product demo — target 2:50, maximum 3:00

Status: script prepared; recording pending. The deployed offline workflow through holdout was checked in a browser on 2026-10-05; the actual recording machine still needs a dry run. Follow [the complete recording guide](DEMO_RECORDING_EN.md) for exact buttons, Mac capture controls, timing and spoken text. Show the unchanged seed-33 SYNTHETIC reference. Do not change the threshold, fees, delay, universe or seed to improve the demonstration's returns.

## Prepare before recording

1. Open **Audit hypothesis** at `/audit/` and allow the local engine to load. Select the default synthetic demonstration and enable **Offline audit** for the first dependable recording path. This mode needs no wallet and keeps its lock on this device.
2. Open the actual [REAL-study status](../REAL_STUDY.md) or [first ingestion report](../../research/real-access-2026-10-03/research_report.md) in a readable editor. It is evidence of genuine ingestion and a blocked study, not a real performance result. Do not display provider keys or account screens.
3. Make a dry run without changing parameters. Measure training/holdout runtime on the recording machine. If waiting cannot fit, use a completed saved attempt and say it was computed before recording; show its manifest/history rather than pretending a calculation is live.
4. Prepare a terminal and an empty directory for the exported ZIP. A real export should be unpacked and rerun. If this cannot fit in the video, show the actual prepared reference rerun, identify it as the reference bundle, and test the fresh browser export separately.

## Screen sequence and spoken text

The clock budgets include clicks and computation; they are targets, not verified recording durations. Speak only the final column.

For today's recording, [DEMO_READ_EN.txt](DEMO_READ_EN.txt) provides shorter spoken paragraphs in the same seven-screen order, leaving more time for clicks. Rehearse it with the actual machine; use its shorter narration with the screen actions below.

Use **Your next step** for training, freeze, holdout and export. Open **Review or edit study setup** to show universe/quality/costs/dates. Use **Read training results** and **Read the final result** to reach evidence. Export performs an exact-value rerun check; include that actual wait in the rehearsal, or show an honestly identified prepared bundle if necessary.

| Time | Screen action | Spoken text |
|---|---|---|
| 0:00–0:15 | Audit hypothesis; point to the hypothesis and SYNTHETIC label. | “We are testing whether wallet accumulation beats comparable baselines after costs. This is our unchanged synthetic demonstration, clearly labeled. It is not real Solana profitability.” |
| 0:15–0:35 | Briefly show the actual REAL-study report; return to the audit's quality, provenance and dataset hash. | “We also retrieved genuine transactions and historical prices. Five sells matched independent RPC records. But required prices are incomplete and historical liquidity is denied, so real performance is blocked. We will demonstrate the full workflow using synthetic observations.” |
| 0:35–0:58 | Show selected universe, dates and execution assumptions; click **Inspect training vs benchmarks**. | “The universe, dates, capital and execution assumptions are explicit. All three portfolios use one engine. We inspect training and seven pre-specified sensitivity rows; the grid never selects parameters using holdout returns.” |
| 0:58–1:20 | **Freeze this configuration**; open **Immutable experiment manifest** and point to the hash and attempt history. | “Now we freeze the snapshot. Changing a parameter creates another attempt. In this offline mode, the lock is device-local. It prevents accidental edits through the app, but does not independently timestamp or certify the study.” |
| 1:20–1:52 | **Evaluate locked historical holdout**; show the three portfolios and exact net-equity curves. | “On the separate period, the strategy makes about one point three percent gross, but loses one point nine percent net. Buy-and-hold makes four point two percent net; momentum loses eight point nine. Exposure, turnover and trade counts differ, so these results do not establish alpha.” |
| 1:52–2:15 | **Inspect portfolio → Inspect a trade**; show signal timing, gross/net, modeled costs and failed-execution evidence. | “Here is the evidence behind a trade: the signal, delayed execution, size, exit and separate costs. Missing required observations block performance. Costs erase this strategy's observed gross return, which is a useful reason to reject the hypothesis in this period.” |
| 2:15–2:50 | **Download reproduction ZIP**; show the actual contents and successful `python3 reproduce.py` rerun. | “The export contains the frozen manifest, permitted observations, exact engine, results, trades, exclusions and report. Another researcher can rerun it and compare fingerprints. Historical holdout data may already be known to the user. The outcome is inspectable evidence, not a promise of profitable trading.” |

## If the full workflow is verified online

An explicitly signed-in hosted demonstration may use server-persisted lifecycle hashes instead of offline locks. Explain that detailed results remain device-local and server persistence does not certify client calculations. Manual Phantom approval is not yet verified here. Do not switch to this path on recording day without a complete dry run.

When a genuine study actually passes data-quality/reconciliation checks, show its own manifest and actual results, even if negative. Replace the blocked-study screen only then; never relabel the seed-33 observations as REAL. Wallet signing, provider retrieval, payment, a devnet receipt and an on-chain transaction are not required for this three-minute audit demonstration.
