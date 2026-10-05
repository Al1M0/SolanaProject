# Current media and earlier source assets

## Use these finished videos

- [Revised team pitch — 1:48](https://d2ol7oe51mr4n9.cloudfront.net/user_3KH1suUw6Ev08L0HRx9TlaLPwnv/d2e364be-2dcf-485e-b73b-dfb7872f9bb8.mp4): introduces Ali and Merey, product motivation and honest research evidence.
- [Product demo — 3:00](https://d2ol7oe51mr4n9.cloudfront.net/user_3KH1suUw6Ev08L0HRx9TlaLPwnv/3073e8de-450f-4848-9a6f-f74412a86eec.mp4): actual public MVP through training, freeze, holdout, trade evidence and export.
- [New pitch narration](https://d2ol7oe51mr4n9.cloudfront.net/user_3KH1suUw6Ev08L0HRx9TlaLPwnv/155c4983-000e-4d36-b04c-509dd621b797.mp3): stock ElevenLabs George, original speed, no participant impersonation.
- [Actual measured media evidence](../FINAL_MEDIA_EN.md) and [new pitch metadata](team-pitch-verification.json).

The form requires YouTube, Loom or Vimeo viewing links. These MP4s are source files to upload; no accepted-host upload or final submission is claimed. The separate Canva draft is not required to use the finished native video.

## Earlier assets retained for transparency

- pitch.mp4 in public GitHub is the earlier 93.709-second explanatory cut and is superseded. The optional render_pitch.py script produces a different 120-second alternate cut; neither is the current team pitch.
- pitch-audio.mp3 is the unchanged original supplied ElevenLabs narration, 92.186 seconds. The product demo still uses this source with disclosed timing edits.
- pitch-poster.png is the existing project graphic. It is not a newly claimed logo.
- mvp-audit.jpg and mvp-holdout.jpg are actual browser screenshots of the public Cloudflare app.
- checksums.json describes the earlier assets, not the newly hosted files. Use team-pitch-verification.json and FINAL_MEDIA_EN.md for current hashes.

## Actual browser evidence

An earlier browser check timed out waiting for a download. A later fresh isolated browser completed the same unchanged SYNTHETIC workflow, saved a 1,112,627-byte export and independently reproduced it on Python 3.12.15. The later successful check is recorded in FINAL_MEDIA_EN.md; no wallet/provider or complete REAL-performance check is implied.

## Render the current pitch

Run python3 scripts/assemble_team_pitch.py narration.mp3 /tmp/team-pitch with the new narration above. Requires native Higgsedit, ffmpeg and a cached faster-whisper small model. Narration boundaries are measured before graphics assembly; narration speed is unchanged. Final duration is measured and must remain at most 120 seconds. Encoder-dependent video fingerprints are separate from research reproducibility.
