# Pitch media and browser verification

## Final submission cuts — 2026-10-05

Use the final [2:00 pitch](https://d2ol7oe51mr4n9.cloudfront.net/user_3KH1suUw6Ev08L0HRx9TlaLPwnv/b1718ded-0e30-4b5c-92ad-a6adde3caf20.mp4) and [3:00 product demo](https://d2ol7oe51mr4n9.cloudfront.net/user_3KH1suUw6Ev08L0HRx9TlaLPwnv/3073e8de-450f-4848-9a6f-f74412a86eec.mp4) for the application. The earlier pitch MP4 stored in the GitHub media directory is superseded. [FINAL_MEDIA_EN.md](../FINAL_MEDIA_EN.md) records exact durations, file hashes and the fresh browser export/strict rerun. The two-minute local renderer described below is an alternate cut; its encoded bytes differ from the hosted final retimed cut.

The later recording actually saved a fresh 1,112,627-byte ZIP and reproduced it on Python 3.12.15. It completed the anonymous Offline audit with the unchanged synthetic configuration. The earlier download timeout described below remains a record of that earlier check; it is no longer the latest export evidence. No real wallet approval, complete REAL study or submitted application is implied.

- `pitch.mp4`: the GitHub media directory retains the earlier **1:33.71** explanatory cut. The optional local renderer produces a separate **2:00.00** alternate cut. Use the final hosted two-minute link above for submission. These are explanatory slides, not the product screen recording.
- `pitch-audio.mp3`: unchanged team-supplied ElevenLabs file, **1:32.19**, SHA-256 recorded in `checksums.json`. It is not represented as a team member's natural voice.
- `pitch-poster.png`: first explanatory slide.
- `mvp-audit.jpg` and `mvp-holdout.jpg`: genuine browser screenshots of the team-supplied Cloudflare deployment on 2026-10-05.

## Checked deployment

The browser opened https://solana-quant.hkakasi358.workers.dev/audit/ without account sign-in. The Python runtime loaded, and the existing default Offline audit path completed training, freezing and chronological holdout evaluation. Its result was +1.28% gross and −1.92% net for the wallet hypothesis, +4.24% net for buy-and-hold and −8.88% net for momentum, consistent with the committed reference after rounding.

The export control reported **“Bundle prepared. Your browser handles saving the ZIP.”** The cloud-browser download event did not return a file before its timeout, so no new downloaded ZIP or strict replay of that particular browser attempt is claimed here. The committed reference reproduction bundle is independently checked by the publication pass. No Phantom, online-provider, hosted D1 or REAL-performance test is implied by this offline check.

## Rebuild the pitch

The optional renderer requires Python, Pillow, DejaVu Sans fonts and ffmpeg:

```bash
python3 scripts/render_pitch.py --work-dir /tmp/solana-pitch
```

Visual text summarizes the prepared pitch script. The original supplied narration is preserved in the MP3. In the MP4, `atempo` slows speech to approximately 0.778× without changing its pitch, and the five evidence slides receive proportionate reading time. The final container is exactly 120 seconds and has passed complete video/audio decoding. The slides are not word-for-word subtitles and their section timings are approximate.

The final pitch and product-demo viewing links are available above. Team identity/event fields and portal submission remain unfinished. If the actual form restricts video hosts, upload the finished final MP4s to its accepted host.
