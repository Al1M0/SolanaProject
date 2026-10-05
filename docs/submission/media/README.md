# Pitch media and browser verification

- `pitch.mp4`: narrated English pitch, 1280×720, H.264/AAC, **1:33.71**. Five explanatory slides with subtle movement and fades; not a screen recording of the product demo.
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

Visual text summarizes the prepared pitch script. The supplied narration is preserved in the MP3 and used for the MP4. The slides are not word-for-word subtitles and their section timings are approximate.

A downloadable MP4 in GitHub is available now. Upload it to the video platform accepted by the submission form for a convenient viewing URL. The product demo recording, team identity fields and portal submission remain unfinished.
