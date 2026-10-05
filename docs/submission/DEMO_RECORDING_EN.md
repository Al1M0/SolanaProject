# Record the product demo — complete operator guide

The [finished 3:00 English demo](https://d2ol7oe51mr4n9.cloudfront.net/user_3KH1suUw6Ev08L0HRx9TlaLPwnv/3073e8de-450f-4848-9a6f-f74412a86eec.mp4) already records the actual public MVP through export and strict fresh-ZIP reproduction. This operator guide is retained for optional future rerecording. The revised [team pitch](https://d2ol7oe51mr4n9.cloudfront.net/user_3KH1suUw6Ev08L0HRx9TlaLPwnv/d2e364be-2dcf-485e-b73b-dfb7872f9bb8.mp4) is exactly 1:48, within the two-minute limit. Both videos still need upload to YouTube, Loom or Vimeo. Use [TODAY_EN.md](TODAY_EN.md) for the remaining steps.

MVP: https://solana-quant.hkakasi358.workers.dev/audit/

The project URL supplied by the active participant is https://colosseum.com/arena/projects/quantlab. Its editable fields, team membership and submission status have not been verified. Only confirmed active participants should be included in the submission; names, roles and public contacts are still pending confirmation.

## 1. Set up the recording

1. Plug in the computer, turn on Do Not Disturb, close unrelated tabs, and open the audit URL in Chrome or Safari. Use a normal readable browser zoom. Hide bookmarks if they distract from the product.
2. Wait for the app to appear. Keep the existing default SYNTHETIC dataset, configuration, token selection, costs and seed. Enable **Offline audit · keep this attempt and its lock on this device**. Its lock is local to the device. Use this path for the recording; it needs no provider key or wallet login.
3. Read the hypothesis near **THE IDEA YOU ARE CHECKING**. Locate **Your next step**, **Review or edit study setup**, and the attempt history near the bottom. The next-step button changes as the attempt progresses.
4. Keep this guide on a phone or a second screen. The recorded picture should show the actual application and any actual exported files being demonstrated.
5. On a Mac, press **Shift–Command–5**, choose **Record Selected Portion**, and frame the browser's product content. Under **Options**, select the microphone if reading the English narration live. Select Desktop or another known folder as the save destination. Stop from the menu-bar recording button or **Command–Control–Esc**.
6. Record a ten-second sample first, stop it, and play it. Check that the app's text is readable and the voice is clear. If separate narration will be added later, record the picture without microphone audio and provide the English voice file separately. Do not assume a recording without a selected microphone contains speech.

Apple documents these screen-recording and microphone controls at https://support.apple.com/ru-ru/102618 (checked 2026-10-05).

## 2. Rehearse once before recording the final take

Run the exact sequence below before recording. Time training, holdout and export on your own computer. The export performs a verification calculation and may take time. Check that a real ZIP appears in Downloads; the on-page message alone does not demonstrate that a download was obtained.

For a new live recording, reload the audit page before starting and enable Offline audit if necessary. Do not restore the completed rehearsal attempt when narrating a new live calculation. Browser storage retains previous attempts; reloading does not erase their history. Let the page finish loading, then begin the recording.

If your rehearsal cannot fit in three minutes, use the completed saved attempt honestly: click **Inspect attempt** in the attempt history, show its frozen settings and actual results, and say: **“This attempt was computed before recording. I will show its saved configuration, results and export.”** Do not describe restored results as a new live computation. Another option is an edited recording with a visible **“Computation wait shortened”** caption over any cut waiting time. Keep the actual result and attempt identity consistent.

## 3. Follow this screen sequence

The times are recording budgets, not measured durations. Read only the quoted English narration. Keep the cursor calm, pause on evidence, and avoid scrolling while saying an important number.

### 0:00–0:15 — Introduce the audit

Start at the top of the audit page. Show the hypothesis and visible **SYNTHETIC** label. Leave enough of the page visible to establish which application is being used.

> This is Solana Quant Research Lab. We test whether a wallet signal beats simple baselines after costs. This demonstration uses clearly labeled synthetic data. It shows the workflow, not real Solana profitability.

### 0:15–0:40 — Show the study setup

Open **Review or edit study setup**. Briefly point to the dataset and selected tokens, price/liquidity coverage, capital, fees, entry delay and training/holdout dates. Keep the defaults unchanged. Collapse the setup or scroll back to **Your next step**, and click **Inspect training vs benchmarks** once.

> The selected tokens, historical periods, capital, fees and execution delay are explicit. We keep this configuration unchanged. The wallet strategy, buy-and-hold and fixed momentum use the same execution engine.

### 0:40–1:03 — Inspect training

Wait for the progress display to finish. Click **Read training results** to reach the earlier-period comparison. Show its portfolio results and the **Training-only sensitivity · all seven rows** table. Do not select a profitable row or change settings.

> Training compares the hypothesis with both baselines. These seven sensitivity rows are pre-specified and use only the training period. The app does not select settings from later-period returns.

### 1:03–1:23 — Freeze the configuration

Return to **Your next step** and click **Freeze this configuration**. Once complete, find **This snapshot is locked** and expand **Immutable experiment manifest**. Point to the manifest hash, frozen hash and recorded configuration; briefly show the attempt history if visible.

> Now we freeze the configuration. A change creates another attempt rather than replacing this one. This offline lock stays on this device. It prevents accidental edits through the workflow, but is not an independent timestamp.

### 1:23–1:55 — Evaluate the holdout

Return to **Your next step** and click **Evaluate locked historical holdout**. Wait for it to complete. Click **Read the final result**. Show the portfolio comparison and equity chart. Keep the after-cost return column visible while reading the figures.

For the unchanged seed-33 reference, the rounded holdout values are wallet strategy **+1.28% gross / −1.92% net**, buy-and-hold **+4.24% net**, and momentum **−8.88% net**. Read the actual screen if a value differs, and investigate an unexpected difference before uploading the take.

> On the later period, the wallet strategy gains about one point three percent before costs, but loses one point nine percent after costs. Buy-and-hold gains four point two percent net. Costs erase the wallet strategy's observed gain. These synthetic results do not prove alpha.

### 1:55–2:20 — Show one trade

Use **Inspect portfolio**, select the wallet strategy if the interface asks, then **Inspect a trade**. Show one actual trade's signal, delayed entry, exit, gross/net result and cost breakdown. Keep the displayed trade selected; do not imply that an individual trade is the whole strategy result.

> Here is the evidence behind one trade: its signal, delayed entry, exit and modeled costs. We inspect the timing and costs instead of relying on a headline return. Exposure, turnover and trade counts also differ across portfolios, so we make those differences visible.

### 2:20–2:50 — Export the evidence

Return to **Your next step**, or use the export panel, and click **Download reproduction ZIP** once. Wait for export verification and **Bundle prepared. Your browser handles saving the ZIP.** Check the actual download in the browser or Finder. If it has finished, open the downloaded ZIP and show the real extracted files, including `reproduce.py`. Do not show a reference archive as if it were this attempt's new export.

> The export includes the frozen manifest, permitted observations, exact engine, results and trade evidence. Another researcher can run the reproduction script and compare fingerprints. Genuine transaction ingestion is available, but complete real performance remains blocked by price and liquidity coverage.

Stop the recording by 2:50–3:00. If export is still running, complete it outside the timed take and use a clearly disclosed saved-attempt recording. Never announce a successful download or reproduction that did not occur.

## 4. Optional: demonstrate the real rerun

This is useful evidence, but do it only if already tested and it fits the three-minute video.

1. Double-click the actual ZIP in Finder to extract it. Find the folder containing `reproduce.py`.
2. Open Terminal. Type `cd ` including the trailing space, drag that folder from Finder onto Terminal, and press Enter. Finder supplies the escaped path.
3. Run:

```bash
python3.12 reproduce.py
```

4. Show the actual output, including `"reproduced": true`, only after this run succeeds. Use Python 3.12 for exact results. If it is unavailable, do not claim that a new rerun succeeded. The finished demo's actual fresh export has already been strictly verified on Python 3.12.15; see FINAL_MEDIA_EN.md.

## 5. Review, upload and hand off

Play the complete exported video. Confirm actual application footage, English narration, a visible SYNTHETIC label, readable evidence and no private account screens. Runtime must not exceed 3:00. Use the revised 1:48 team pitch linked above; the older GitHub media/pitch.mp4 is superseded. The new pitch uses stock George AI narration without stretching its speed.

Upload the final videos using the platform accepted by the actual application. On YouTube, **Unlisted** permits anyone with the link to watch without a Google account; **Private** restricts viewing. Check the final viewer URLs while signed out. YouTube's controls are documented at https://support.google.com/youtube/answer/157177?hl=en (checked 2026-10-05).

Supply the demo viewing URL, measured duration and confirmed active-participant details for the README and application. The GitHub source and public MVP are already available. A project page URL by itself is not submission confirmation.

Official submission requirements: https://colosseum.com/hackathon?year=fall2026 (checked 2026-10-05). The participant's organizer message additionally requires all four items and English materials.
