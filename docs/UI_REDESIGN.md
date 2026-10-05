# Research desk interface — 2026-10-04

The independent researcher needs to answer one question: does a wallet hypothesis beat comparable baselines after costs on a separate historical period? The interface gives that question a visible home and makes the evidence easier to inspect.

## Source-linked design references

- [Linear's official 12 March 2026 UI refresh](https://linear.app/changelog/2026-03-12-ui-refresh): consistent headers, navigation and controls, with a quieter sidebar that leaves attention on the work. Applied as grouped navigation, consistent spacing and a clearer page hierarchy.
- [Nansen's official site](https://nansen.ai/): signal-led presentation and prominent typography. Used as a composition reference only. No claim about competitors' research functionality or feature absence follows from this design review.

Both primary pages were checked on 2026-10-04. This is an original implementation using the existing React, CSS, Lucide and Recharts stack. No competitor logo, screenshot, illustration or downloaded asset is embedded.

## Changes

1. A charcoal research desk, mint/violet accents, warmer display typography and a readable 12/14/16px supporting scale. Existing routes inherit the shared controls, tables, surfaces and focus states.
2. One reference-hypothesis action beside actual dataset coverage and REAL/SYNTHETIC labeling. Counters distinguish exploratory backtests from frozen audit experiments.
3. Research and on-chain navigation groups, current-page semantics and a skip link. Small-screen navigation retains text labels and horizontal scrolling.
4. Actual lifecycle stages, a study sheet with current capital/universe/costs/split, and distinct freeze/export sections.
5. Training and holdout results show three net-equity curves, gross/net return cards, modeled costs, plain-language findings, the full exposure/turnover/failure table and trade evidence. The plot joins exact timestamps and leaves absent values null; invalid portfolios supply no performance curve. It neither interpolates missing observations nor fills from future data.

6. A follow-up button pass adds mint gradients, restrained hover lift, press feedback, clearer focus rings, pill-shaped wallet controls and selected tab accents. Transitions take 160–180ms; page headings and result cards enter in 240–260ms. Hover effects are limited to precise pointers, disabled actions stay inert, and reduced-motion settings disable movement and pseudo-element transitions. No interaction library or click handler was added.

The first two appearance passes left the engine, immutable persistence, seeds, benchmark definitions, default configuration, provider adapters and reference artifacts unchanged. The negative SYNTHETIC result remains negative.

## Guided follow-up after actual builder screenshots

The builder reached training, freeze, holdout and export, but still could not understand the workflow or red provider errors, and requested stronger animation. The new **Your next step** panel offers one prominent action based on persisted status. **Review or edit study setup** keeps the universe, quality, costs and dates inspectable without presenting all controls immediately. Result views lead with **In plain words** and the before/after-cost comparison. Trade selection now shows signal, modeled entry/exit and costs as a readable record, with exact JSON still available.

Buttons have a finite light pass on hover and tactile press feedback. The next-step panel, three portfolio cards, current lifecycle mark, details and selected trade have finite 300–600ms transitions; the exact chart is revealed in 850ms. Only an actually running operation has a subtle repeated glow. Motion never increments returns, fills missing marks or fabricates progress. Reduced-motion and print variants stay static.

Markets replaces unexplained red text with an amber unavailable state, a retained exact provider response, a manual retry and an audit link. Current SOL can fall back to an actual wSOL pool quote through the existing adapter, with visibly different provenance; configured Birdeye access can supply actual closed-hour display history. Neither change supplies missing historical liquidity or unblocks the genuine study by itself.

The supplied browser export exposed a JSON float/int hash mismatch even though every numeric result matched. The export adapter now verifies a frozen rerun and restores Python's exact numeric representation without changing the engine, dataset, manifest or results. The corrected study passed independent CLI reproduction; see [verification](VERIFICATION.md).

## Verification boundary and human task

Automated checks can verify result values, preservation of warnings, builds and data gaps; they do not establish a pixel-perfect or fully usable browser layout. The managed Sites environment requires the unavailable `control-browser` skill for visual interaction; its preview instructions prohibit an alternate browser-control path. No browser screenshot or manual wallet approval is claimed.

Before recording the demo, open the published app in Chrome or Safari:

- At laptop width and 390px phone width, check labeled navigation, readable inputs, horizontal comparison-table scrolling, disclosures and visible keyboard focus.
- In Audit hypothesis, inspect seed-33 data, run training, review all sensitivity rows, freeze, evaluate the holdout, inspect a strategy trade and download the reproduction ZIP.
- Confirm the reference holdout strategy remains +1.2818% gross / -1.9150% net; buy-and-hold +4.2418% net; momentum -8.8826% net. The displayed findings must explain costs and limitations.
- Edit one configuration control: the visible result must reset to a new draft while the earlier attempt remains in the log. Restore the frozen attempt and check that an already evaluated holdout cannot be evaluated again.
- Run the built static demo with Offline audit enabled and reproduce the exported ZIP using `python3 reproduce.py`.

Record further real feedback in the existing feedback log. The builder screenshots and export are recorded separately from the five still-empty independent interview slots. No participants, timings or customer success are invented.
