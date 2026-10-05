# Colosseum form — copy-ready English answers

Prepared from the team's actual Media and code screenshots on 2026-10-05. This document does not save or submit the application. The videos must be hosted on **YouTube, Loom or Vimeo**; direct MP4 download links are source files, not accepted-host submission links.

## GitHub link

https://github.com/Al1M0/SolanaProject

## Please share any important context about your repo

The repository contains the app, research engine, adapters, tests and reproducibility artifacts. It extends an existing codebase; development history and Codex assistance are disclosed in docs/submission/DEVELOPMENT_HISTORY.md. The demo is SYNTHETIC. Genuine transaction and price ingestion is documented, but complete REAL performance is blocked by missing prices and historical liquidity.

This answer is below the visible 500-character limit.

## Please submit a demo video of your product

Upload the finished three-minute product demo to YouTube, Loom or Vimeo, then paste that video's actual viewing link here. The file is available from [the submission link sheet](LINKS_TO_SUBMIT_EN.md). It shows the actual MVP, with timing edits and explanatory cards disclosed; it does not claim real performance.

Suggested English upload title: **QuantLab — Product Demo | Colosseum 2026**

## Live product link

https://solana-quant.hkakasi358.workers.dev/

## Access instructions

No login, wallet connection or API key is required for the offline demo. Open Audit hypothesis, enable Offline audit, then follow Training → Freeze → Holdout → Export. The demonstration uses clearly labeled synthetic data.

## Pitch video

Upload the revised team-introduction pitch to YouTube, Loom or Vimeo, then paste that video's actual viewing link here. It introduces Ali and Merey, explains the product, shows the unchanged synthetic finding and discloses the blocked real study. Do not use the earlier product-only pitch.

Suggested English upload title: **QuantLab — Team & Product Pitch | Colosseum 2026**

## X profile

Optional. Leave blank unless the team has an actual public X account it wants to include. No account is invented here.

## Project logo or graphic

Upload `docs/submission/media/pitch-poster.png` as the project graphic. The existing PNG is below the visible stored-image limit; it is a graphic, not a claimed newly designed logo.

## About the project — replacement for the outdated trading-platform description

QuantLab helps Solana researchers audit wallet-based trading hypotheses against buy-and-hold and fixed momentum benchmarks after modeled costs. It combines chronological training and holdout evaluation, frozen configurations, trade evidence and reproducible exports. The working demo uses clearly labeled synthetic data. Genuine ingestion is documented; complete real performance remains blocked by missing prices and historical liquidity.

## Team introduction — only confirmed active participants

Ali Mukhanbetov is a second-year Information Systems student at KBTU in Almaty. Mukhametkali Merey is interested in quantitative trading, Python and blockchain. They are building an inspectable tool for testing wallet-based trading ideas. This is not a claim of verified customer demand or professional research experience.

Both participants must complete their own submission profiles. Personal profile questions, exact task division and private/contact information not shown in the supplied screenshots remain for the participants to answer factually.

## Save versus submit

The screenshots say final submission opens **October 6 at 4:00 AM PDT**, equivalent to **October 6 at 4:00 PM in Almaty**. Before opening, complete the materials and click **Save draft**. Saving a draft is not submission. The team's separate organizer deadline tonight still applies to preparing/delivering the materials. A later final-submit confirmation is not yet recorded.

## Project details — exact form supplied by the team

Suggested submission copy, checked against the displayed character limits. This does not fill or submit the portal. Telegram and meaningful human contributions outside the current team remain unconfirmed; do not submit a blanket claim that no other person contributed.

### Project name

QuantLab

### Brief description — 245 / 500 characters

QuantLab helps Solana researchers audit wallet-based trading hypotheses against buy-and-hold and fixed momentum after modeled costs. Freeze a configuration, evaluate a historical holdout, inspect trades and export reproducible research evidence.

### Project website

https://solana-quant.hkakasi358.workers.dev/

### What are you building, and who is it for? — 793 / 1000 characters

QuantLab is a research tool for independent Solana researchers who currently validate wallet-based trading ideas manually. It asks whether a hypothesis outperforms comparable baselines after modeled fees, delays and liquidity constraints on a separate period. Users select wallets and tokens, inspect data quality, run training and a pre-specified sensitivity grid, freeze the configuration, then evaluate a historical holdout. Strategy and benchmarks share one execution engine. Results include gross/net returns, costs, drawdown, exposure, turnover and individual trades. A reproducibility export contains the manifest, permitted data, engine, results and report. The working demo is explicitly SYNTHETIC; complete REAL performance remains blocked by price and historical-liquidity coverage.

### Why did you decide to build this, and why build it now? — 623 / 1000 characters

We chose this project to turn our interests in quantitative trading, Python and Solana into a practical research workflow. Successful wallets can suggest ideas, but their activity alone does not show whether following them works after costs and delays. We wanted to make assumptions inspectable and make rejecting a weak hypothesis a useful outcome. The hackathon gives us a focused deadline to build and test the prototype. We have a working audit and genuine ingestion evidence. Next, we will complete the real study and test the workflow with five independent researchers. Customer demand and pricing remain unvalidated.

### What technologies are you using or integrating with to build your product?

Next.js, React, TypeScript and CSS for the interface; a portable Python execution engine and Pyodide web worker for the offline browser audit. The repository also includes FastAPI, SQLAlchemy, Alembic and SQLite for the native API, plus a Cloudflare Worker/D1 path with Drizzle for hosted services. Integrations include Helius, Solana RPC, Birdeye, DEX Screener and CoinGecko; Phantom supports optional signed-message login. GitHub stores the code and research artifacts. Regression tests and Playwright browser checks support verification. OpenAI Codex provided substantial implementation, testing and documentation assistance. Canva and Higgsfield were used for submission visuals/editing, and ElevenLabs for disclosed AI narration.

### Which chains does your product use?

Select **Solana only**. No other chain is integrated into this submission.

### How does your product use these chains? — 396 / 500 characters

We ingest Solana wallet transactions through Helius and check selected swaps against independent public RPC records. Token mints, timestamps and swap flows are normalized and joined to historical market observations. Our engine models costs, delays and liquidity constraints to audit wallet hypotheses. This is off-chain research: the product does not submit trades or deploy an on-chain program.

### Category

DeFi

### Is your project a mobile-focused dApp?

No. It is a browser-based research workflow; no dedicated mobile dApp is claimed.

### Where is your team primarily based?

Kazakhstan. The screenshot-confirmed public location for Ali is Almaty. The form asks for country.

### Team Telegram contact

Enter a real reachable team contact, such as the actual participant's @username. No contact was supplied to Codex; no account is invented here. Verify in Telegram Settings before entering it.

### Did anyone not listed on the team do meaningful work? — AI/history disclosure, 337 / 600 characters

Substantial AI assistance came from OpenAI Codex for implementation, regression tests, verification and documentation. Canva, Higgsfield and ElevenLabs supported submission media. The project extends an existing repository; baseline history, reused modules and AI-assisted changes are disclosed in docs/submission/DEVELOPMENT_HISTORY.md.

This paragraph discloses confirmed AI assistance and the existing baseline. It does **not** settle human attribution. If a former participant or another person wrote code or otherwise made a meaningful contribution, the team must add their real name and contribution, even when they are not an active teammate. Codex has not been given evidence identifying such human contributors. Confirm this part before final submission.

### Anything else judges should know?

Our demonstration uses unchanged, clearly labeled SYNTHETIC data. The wallet hypothesis returns +1.28% gross but -1.92% net, versus +4.24% net for buy-and-hold. This illustrates a rejected hypothesis, not proven alpha or real profitability. Genuine Solana transactions and historical prices were retrieved; five sells matched independent RPC records. Complete REAL performance is blocked by missing prices and historical exit liquidity. A historical holdout may already be known to a user, and offline locks are device-local. The fresh demo export reproduced exactly on Python 3.12.15; Python 3.11 can fail exact float hashes. Interviews and pricing validation are pending. We do not claim customers, revenue or partnerships.
