# Recording and GitHub handoff

Source, research evidence and pitch media are published in [Al1M0/SolanaProject](https://github.com/Al1M0/SolanaProject). The prepared pitch is a 1:34 slide video using the supplied ElevenLabs narration. A separate product demo and external video viewing links remain pending. All spoken narration, subtitles and repository submission copy must be English.

## Record two separate videos

1. Use [PITCH_EN.md](PITCH_EN.md) for a two-minute presentation and [DEMO_EN.md](DEMO_EN.md) for a separate demo under three minutes. Read both aloud before recording; the time markers are rehearsal budgets, not measured video durations.
2. If recording on a Mac, press **Shift–Command–5**, choose the screen/area to record, and use **Options → Microphone** to select the actual microphone. Record a ten-second sample, replay it and confirm readable app text and audible narration. [Apple's official screen-recording guide](https://support.apple.com/en-us/102618) documents the controls.
3. Record the pitch with a simple product visual and the real speaker. Record the demo with the visible SYNTHETIC label, normal browser zoom and no parameter tuning. Follow the prepared live/saved-attempt disclosure if computation is pre-run.
4. Replay the final exported files from start to finish. Measure their actual duration. The pitch target is 2:00; the demo must not exceed 3:00. Re-record/edit for clarity and timing without disguising a failed operation as a successful live one.
5. Upload both videos using the hosting/access method accepted by the actual submission portal. Test each link as a viewer without the uploader's account. Insert the genuine links in README and the application. Do not use script links as video links.

No generated narration, staged wallet transaction, invented customer quote or profitable-only retuning is necessary for the submission.

## Provide a real GitHub destination

1. Sign into the human team's GitHub account. Create a new repository named `solana-quant-research-lab` under the intended owner. If importing this source, do not pre-populate README, .gitignore or a license; these choices otherwise introduce conflicts or an unchosen license.
2. Choose repository visibility consciously. The official Colosseum FAQ encourages public repositories and also permits private repositories with review access according to its current instructions. This document does not send invitations or grant access.
3. Send the repository URL to the coding assistant so an explicitly authorized GitHub connection can be used, or publish from a local authenticated Git/GitHub Desktop environment. Do not send an API key or password in chat. The current destination is the public Al1M0/SolanaProject repository; the source import is published there.
4. Publish actual source files with the prepared root README, not just the release ZIP or compiled application. Retain disclosure of prior code and AI-assisted work. If the release ZIP is the only available local source, extract it and exclude the generated `frontend/out` directory before initializing the GitHub repository. Never include local databases, private environment files or raw provider observations. The package already excludes credentials and dependencies.
5. Fill only confirmed team fields and add the actual video URLs. Add an actual current screenshot if wanted. Do not copy the example's team, Rust/Anchor stack, MIT badge, CI badge or performance claims.

### If publishing the extracted source with local Git

Run these commands from the extracted project directory. They create a local repository only when the archive has no `.git`; use the actual checkout/history instead if available. Local Git identity and GitHub authentication must already be configured. Replace `TEAM_OWNER` with the real owner before the remote step.

```bash
git init -b main
git add .
git diff --cached --stat
git commit -m "Prepare Solana Quant Research Lab submission"
git remote add github https://github.com/TEAM_OWNER/solana-quant-research-lab.git
git push -u github main
```

An extracted ZIP has no original Git commit objects. Keep [DEVELOPMENT_HISTORY.md](DEVELOPMENT_HISTORY.md); if using this path, say the GitHub repository imports the existing source and do not treat its first import commit as the beginning of development. The original Site repository remains the history evidence. Public GitHub publication does not grant a software license or broaden provider-data permission.

Sources checked 2026-10-04: [create a GitHub repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository), [add locally hosted code](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github), [official Colosseum FAQ](https://colosseum.com/hackathon?year=fall2026), and the [organizer's example](https://github.com/Marakaya/colosseum_example).

## Make the MVP reviewable

The public MVP at https://solana-quant.hkakasi358.workers.dev/ was checked in a browser on 2026-10-05. The offline training, freeze and holdout flow completed with the SYNTHETIC label visible. The export control reported that its bundle was prepared; that browser download was not independently replayed. The committed reference archive was separately extracted and reproduced successfully. See media/README.md for evidence. A free alternate address is covered in DEPLOY_WITHOUT_CHATGPT_EN.md.
