# Final submission media — actual evidence

Prepared 2026-10-05. All videos are English. These materials do not submit the application.

| Final file | Public viewing link | Duration | Format | Bytes | SHA-256 |
|---|---|---:|---|---:|---|
| Pitch | [Watch pitch](https://d2ol7oe51mr4n9.cloudfront.net/user_3KH1suUw6Ev08L0HRx9TlaLPwnv/b1718ded-0e30-4b5c-92ad-a6adde3caf20.mp4) | 120.000 seconds | H.264/AAC, 1280×720 | 3545081 | `4582c8d9577258bc035334544878f9243239b14c119d3451a9666325f87a1893` |
| Product demo | [Watch demo](https://d2ol7oe51mr4n9.cloudfront.net/user_3KH1suUw6Ev08L0HRx9TlaLPwnv/3073e8de-450f-4848-9a6f-f74412a86eec.mp4) | 180.000 seconds | H.264/AAC, 1280×720 | 5495840 | `5ef746c6d33ae7734a08e28fb18004147aae8e71783755ad586e9f1a04524ab9` |

Final media uploads returned HTTP 200 and were confirmed. The published MP4s were independently downloaded. Full video/audio decoding and durations were checked. Eight demo timeline frames were visually inspected for labels, readability and actual evidence. ASR checked the original supplied narration and its paragraph boundaries; no full human listening review is claimed. The team should listen to both complete videos before submitting.

Both use the original team-supplied ElevenLabs narration, with tempo edits and no claim of a team member's natural voice. The demo was composed with native Higgsedit from actual Playwright screen capture. The app footage was not AI-generated. The pitch uses explanatory slides; it is separate from the product screen recording. The earlier GitHub pitch MP4 is superseded by the final two-minute hosted cut.

## Actual demo sequence

| Final time | Evidence |
|---|---|
| 0:00–0:20 | Actual public MVP, audit hypothesis and visible SYNTHETIC disclosure |
| 0:20–0:50 | Labeled explanatory card: committed real ingestion status, missing required prices and denied historical exit liquidity |
| 0:50–1:08 | Actual default configuration, universe, costs and chronological split; no edits |
| 1:08–1:31 | Actual training and seven pre-specified training-only sensitivity rows |
| 1:31–1:48 | Actual frozen snapshot and expanded immutable manifest |
| 1:48–2:20 | Actual later-period evaluation versus buy-and-hold and fixed momentum after costs |
| 2:20–2:36 | Actual selected modeled trade and cost evidence |
| 2:36–2:43 | Actual export verification and fresh ZIP download |
| 2:43–3:00 | Clearly labeled report rendering the completed independent Python rerun |

All timing is edited and disclosed in the video header. Computation waits are visibly marked as shortened. The status card is not an app screen, complete REAL performance or a new provider request. The verification report is not a simulated terminal: it renders actual successful CLI output and says so.

## Fresh browser export

The browser opened https://solana-quant.hkakasi358.workers.dev/audit/ without account sign-in in a fresh isolated context. Default SYNTHETIC seed 33, capital, universe, fees, delay and threshold were unchanged. It completed training → freeze → holdout → trade inspection → export.

- ZIP download: 1,112,627 bytes, SHA-256 `fe5ceb85875c4d8c5cda8454575781d8a95653dab976ee4b0538cd1b0a0263c1`.
- Actual experiment: `exp_84e27355fa7714857b8a7fde`.
- Frozen manifest: `cc7e401c5f72706164cbc6882c310fec134d117e1e61d21561b6c36ca77b3ef0`.
- Full result hash: `55828634a0d74dfbaee86a5daaa789fa78bb5d3f00a2c20d4904179d33018e59`.
- Independent unchanged-bundle rerun: **Python 3.12.15, reproduced: true**. Exact source/data/manifest/results checks passed; no tolerance or normalization was added.
- Visible holdout: wallet +1.28% gross / −1.92% net; buy-and-hold +4.24% net; momentum −8.88% net. These are simulated results, not real Solana profitability or proven alpha.

No real Phantom approval, signed-in server/D1 workflow, complete REAL study, customer interview or portal submission is verified by this offline browser run. A separate convenience ZIP of recording evidence could not be produced because automatic approval review reached its usage limit; no such archive link is claimed. The application's own reproducibility export works and was actually downloaded/replayed.

## Repeat the recording

Optional media dependencies: Playwright with Chromium, ffmpeg, Pillow/DejaVu fonts, native Higgsedit, faster-whisper with its small model and Python 3.12. The media toolchain is optional and not required to launch the application.

```bash
QUANT_REPRO_PYTHON=python3.12 node scripts/record_demo.cjs /tmp/quant-demo
python3 scripts/assemble_demo.py /tmp/quant-demo docs/submission/media/pitch-audio.mp3 /tmp/quant-demo.mp4
```

The recorder refuses missing downloads, changed reference values or a failed exact rerun. Experiment IDs/creation timestamps differ on a new attempt; deterministic research result fingerprints should match. Media hashes depend on encoder/tool versions and are not the experiment's reproducibility criterion. See [runtime compatibility](REPRODUCTION_RUNTIME_EN.md).
