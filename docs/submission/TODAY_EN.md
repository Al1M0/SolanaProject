# Submit today — 2026-10-05

The human team says its entry is due today before night. Check the exact hour and time zone in the team's portal immediately. This checklist follows the four mandatory items in the organizer's message. All submitted copy and video narration must be English.

## Finish the four links

| Item | What is ready | What a human must finish today |
|---|---|---|
| 2-minute pitch | [Spoken text](PITCH_READ_EN.txt), [timed outline](PITCH_EN.md) | Record, replay, check actual duration, upload and test viewer access. |
| Demo under 3 minutes | [Spoken text](DEMO_READ_EN.txt), [click sequence](DEMO_EN.md) | Dry-run the current app, record, replay, upload and test access. |
| GitHub source | English template README, code, tests, research evidence and history | Create/publish the actual repository, add real team fields and video links. |
| Reviewable MVP | [Deployed app](https://solana-quant.hkakasi358.workers.dev/) | Public viewing was enabled and re-read on 2026-10-05. Test as an anonymous viewer. |

Copy the final URLs into [LINKS_TO_SUBMIT_EN.md](LINKS_TO_SUBMIT_EN.md), the root README and the actual application form. Empty fields are deliberately empty; they are not finished deliverables.

## 1. Make the recording path work

1. Open the app's **Audit hypothesis** page (`/audit/`). Check **Offline audit**. Keep the default **SYNTHETIC** dataset and saved configuration unchanged. No wallet or provider key is needed.
2. At **Your next step**, click **Inspect training vs benchmarks** and wait for the real result.
3. Use **Read training results** to inspect it. Click **Freeze this configuration**.
4. Click **Evaluate locked historical holdout**, wait, then **Read the final result**.
5. Open **Inspect portfolio → Inspect a trade** to show actual evidence.
6. Click **Download reproduction ZIP**; wait for the export check, save it and unpack it. In the extracted folder, run `python3 reproduce.py` if Python is available. Use the already verified reference rerun only if you explicitly identify it as the reference, not this fresh download.

Red negative return values mean the idea lost after modeled costs. They are not application errors. The untuned synthetic reference gains about 1.3% gross but loses 1.9% net. Buy-and-hold gains about 4.2% net; momentum loses about 8.9% net. It is useful to reject a hypothesis that does worse after costs. These are simulated results, not real trading performance or proven alpha.

For quality, dates, universe and costs, open **Review or edit study setup**. Do not change settings after viewing the holdout to make the video profitable.

Make this dry run before recording. If computation does not fit the demo's time budget, show the saved attempt and say: **“This attempt was computed before recording; here are its saved settings and evidence.”** Do not fake a live calculation or hide a failure.

## 2. Record two separate English videos

Read only [PITCH_READ_EN.txt](PITCH_READ_EN.txt) for the pitch. Follow the [demo screen sequence](DEMO_EN.md), reading the corresponding paragraphs in [DEMO_READ_EN.txt](DEMO_READ_EN.txt). The timestamps are budgets, not verified recording durations.

On Mac: **Shift–Command–5 → recording area → Options → Microphone → Record**. Stop using the menu-bar stop button. Record and replay a ten-second sound test first. Do not film provider dashboards or keys. [Apple's recording instructions](https://support.apple.com/en-us/102618), checked 2026-10-05.

Replay both completed exports. Aim for a two-minute pitch and a demo around 2:50, never over 3:00. Use a video host accepted by the actual portal. Verify the two URLs without the uploader's session. A script, source archive or screenshot is not a video.

## 3. Publish GitHub without a terminal

Use the **source-only** archive `solana-quant-research-lab-github-source.zip`; the full release also contains generated `frontend/out`, which is unnecessary for this upload.

1. Extract the source archive. Open `https://github.com/new` in the team's account. Use the name `solana-quant-research-lab`. Choose **Public** if the team intends public code review. Create an empty repository without generated README/license files.
2. Use **uploading an existing file** on the empty repository, or **Add file → Upload files**. Upload the **contents** of the extracted project, with `README.md` at the repository root. Do not upload only the ZIP or nest everything in another project folder.
3. GitHub allows up to **100 files per upload** and **25 MiB per file**. Use these three batches; each has fewer than 100 files in this package:

| Batch | Files/folders to drag from inside the project folder |
|---|---|
| 1 | Root files, including `README.md`, `package.json`, `package-lock.json`, plus `backend`, `data`, `db`, `drizzle`, `edge`, `tests` |
| 2 | `frontend`, `scripts` |
| 3 | `docs`, `research` |

4. Commit each batch to the default branch using meaningful English messages. Wait for upload completion before leaving. Hidden `.gitignore` and `.openai` files are included in the archive; on Mac use **Shift–Command–Period** to show hidden files if needed. Confirm both are retained. Do not add any personal `.env`, database, dependency folder or API credentials.
5. Confirm the root README renders, `frontend/package.json`, `backend/app/engine.py`, `docs/VERIFICATION.md` and `research/reference/reproduction.zip` are browsable. Fill real team names/roles/public contacts and the two real video URLs in README. Commit the edits.
6. Open the repository URL as a viewer. If private, follow the competition's actual reviewer-access instructions instead of assuming judges already have access.

This imports source from the existing project; it does not recreate the original Git history. Keep [DEVELOPMENT_HISTORY.md](DEVELOPMENT_HISTORY.md) and disclose the earlier baseline/AI assistance. The first GitHub upload is not the project's creation date. [GitHub's upload limits and steps](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository), checked 2026-10-05.

## 4. Verify access and submit

The user requested viewer access on 2026-10-05; public viewing was enabled and confirmed through the hosting service. Test the actual URL from a private window/second account and run the offline audit there. No fresh anonymous-browser check is claimed. For the user-selected free alternate address, follow DEPLOY_WITHOUT_CHATGPT_EN.md; the prepared static ZIP does not migrate server/provider functions.

Paste the four actual links and genuine team details into the portal. Preview the application, test every link, submit before the real cutoff and save the real confirmation. This checklist does not register the team or submit on its behalf.

## What to say about unfinished research

“Our end-to-end demonstration is synthetic. We retrieved genuine Solana transactions and historical prices, but missing price coverage and denied historical-liquidity access block real performance. The next step is to complete that study and test the workflow with independent researchers.”

Do not wait for Birdeye, purchase access, rename simulated observations REAL, invent five interviews or add features today. Optional wallet interaction, prospective paper runs and devnet receipts remain unverified or future work. Existing automated tests/build/reproduction checks passed in the preceding implementation pass; the new texts change no product or experiment behavior. Fresh browser usability, recordings and external reviewer access still require the actual human checks above.
