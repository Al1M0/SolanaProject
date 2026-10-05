# First browser usability pass

Status: the builder supplied screenshots of training/holdout plus a saved export, and reported confusion about the workflow/HTTP 403 and weak animation. This evidence led to repairs documented in [FEEDBACK_LOG.md](FEEDBACK_LOG.md). The updated interface still needs a new manual pass. The five independent researcher interviews in [INTERVIEWS.md](INTERVIEWS.md) remain unperformed.

## Task — 5–10 minutes

Open the [MVP](https://solana-quant.hkakasi358.workers.dev/). Go to **Audit hypothesis**, enable **Offline audit**, and keep the default synthetic dataset, universe and configuration unchanged. The device-only lock needs no wallet/provider access. Wait for engine loading; report any actual failure.

Use the prominent **Your next step** action throughout. **Read training results** / **Read the final result** move directly to evidence. Open **Review or edit study setup** only to inspect the configuration; preserve the untuned defaults.

1. Explain what is being tested and whether the dataset is REAL or SYNTHETIC. Find price/liquidity coverage; open **Review or edit study setup** to inspect the chronological split.
2. Click **Inspect training vs benchmarks**. Find the training comparison and seven sensitivity rows. Say what changes after costs and what the baselines mean.
3. Click **Freeze this configuration**. Open **Immutable experiment manifest**. Explain the meaning and limits of the lock.
4. Click **Evaluate locked historical holdout**. Compare net results for the strategy, buy-and-hold and momentum. Explain whether the strategy beat buy-and-hold and why this does not prove alpha.
5. Open **Inspect portfolio**, then **Inspect a trade**. Find one concrete cost and signal/execution timestamp.
6. Click **Download reproduction ZIP**. Export first verifies a mechanical rerun of the saved snapshot without changing its settings. Confirm a real file downloaded. Unpack it in a new directory and run `python3 reproduce.py` if Python is available. Record success or the actual error; a download alone is not a verified rerun.

Do this first pass on the machine used for the recording. Report whether the layout works at your normal browser size, buttons clearly show the next step and animation feels restrained. A phone-size check and a second-account MVP-access check are separate follow-ups. Wallet login is a separate optional pass after the main audit works.

## Send back these observations

| Prompt | Actual response — empty until received |
|---|---|
| First point where you had to guess the next step | |
| Anything that failed, including exact screen text | |
| One sentence explaining the holdout result after costs | |
| Three changes you most want, in priority order | |
| Buttons/animation: too weak, comfortable or distracting; concrete example | |
| Browser/device and ZIP rerun result | |

A screenshot is useful only when it shows the actual confusing/error state; do not spend time collecting screenshots of every page. Preserve actual feedback in [FEEDBACK_LOG.md](FEEDBACK_LOG.md), distinguish suggested changes from implemented repairs, and do not mark a session successful without evidence.
