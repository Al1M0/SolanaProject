# A free address without chatgpt.site

On 2026-10-05 the user requested viewer access and selected a free address. The existing Site's audience was changed to **public** and re-read successfully. Its current URL is still https://solana-quant-research-lab.muhanbetova0101.chatgpt.site. Anonymous browser access still needs a human check.

The prepared Cloudflare Pages ZIP is a **static offline audit**, not a migrated server. It contains the existing browser application, local Python/WebAssembly runtime and the unchanged default SYNTHETIC study. A small script defaults a new browser origin to the existing **Offline audit** mode; it does not alter parameters, observations or research results. Manifest locks and detailed results stay on that browser/device. Real provider APIs, wallet login and server persistence are not part of this package. The original public Site retains those server routes and existing access limitations.

## Upload using the dashboard

1. Create/sign into the team's account at [Cloudflare Dashboard](https://dash.cloudflare.com/). Use the free Pages option; no paid upgrade or domain purchase is needed for this static demo.
2. Open **Workers & Pages → Create application → Get started → Drag and drop your files**. If the dashboard first offers a Worker, select its **Pages** path. These names follow the current official guide; the assistant has not inspected the team's signed-in dashboard.
3. Enter the requested project name, for example `solana-quant-research-lab`. Availability is not confirmed; the actual address may have an added suffix.
4. Upload `solana-quant-research-lab-cloudflare-pages.zip` directly and choose **Deploy site** / **Save and Deploy**. This archive has `index.html` at its root. Do not upload the source/GitHub ZIP for this step.
5. Copy the **actual** successful production URL from Cloudflare. It has the form `<project>.pages.dev`; no specific hostname has been registered by preparing these files.
6. Open the actual URL in a private browser window. Use **Audit hypothesis**, confirm **Offline audit**, keep the default SYNTHETIC settings and complete training → freeze → holdout → trade evidence → export. Replay/reproduce the downloaded export before recording. Check first-load runtime download and local-storage behavior on the recording machine.
7. Add that verified URL to the actual submission and root README. Tell viewers this address demonstrates the offline audit. Do not claim server/provider/wallet migration is completed. No Cloudflare deployment has been performed by preparation alone; a team account/upload is still required.

## Rebuild the upload ZIP

From the project root:

```bash
npm ci
npm --prefix frontend ci
npm run build
python3 scripts/package_pages.py --output ../solana-quant-research-lab-cloudflare-pages.zip
```

The packager checks required local assets, ZIP integrity, file limits and exact research/runtime bytes. It excludes source, databases, server credentials and installed dependencies by packaging only the static output. `standalone-deployment.json` records the source revision and original asset hashes; HTML includes the documented offline bootstrap. These checks are not a substitute for an actual deployed-browser test.

Primary sources checked 2026-10-05: [Cloudflare Pages/free signup](https://www.cloudflare.com/products/pages/), [official Direct Upload instructions and limits](https://developers.cloudflare.com/pages/get-started/direct-upload/), and [Pages platform limits](https://developers.cloudflare.com/pages/platform/limits/). Direct Upload accepts a ZIP/folder and supplies a pages.dev address. A Direct Upload project cannot later switch to Git integration; a separate project is needed for that choice.
