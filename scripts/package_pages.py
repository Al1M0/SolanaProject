"""Package the prebuilt browser audit for a static Cloudflare Pages upload."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BOOT_NAME = "offline-mode.js"
BOOT = b'// Standalone static demo: default to the existing device-only audit mode.\ntry { if (localStorage.getItem("quant.audit.offline") === null) localStorage.setItem("quant.audit.offline", "true"); } catch (_) { /* The audit displays its own storage error. */ }\n'
BOOT_TAG = '<script src="/offline-mode.js"></script>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    public = ROOT / "frontend/out"
    required = ["index.html", "audit/index.html", "research-worker.js", "runtime/pyodide.asm.wasm", "research/engine.py", "research/experiments.py", "research/export_validation.py"]
    if not all((public / name).is_file() for name in required):
        parser.error("Run npm run build first to prepare the browser audit.")
    files = sorted(p for p in public.rglob("*") if p.is_file())
    if any(p.is_symlink() for p in files):
        parser.error("Symlinks are not accepted in a public deployment bundle.")
    if any(p.name.startswith(".env") or p.suffix in {".db", ".pyc"} for p in files):
        parser.error("Unexpected private file in the public output.")
    if any(p.name in {BOOT_NAME, "_worker.js"} for p in files):
        parser.error("Conflicting bootstrap or server worker in the static output.")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    metadata = {"source_revision": revision, "hosting_mode": "static_offline_audit", "default_dataset_kind": "SYNTHETIC", "server_api_included": False, "public_assets_sha256": {p.relative_to(public).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}, "bootstrap_sha256": hashlib.sha256(BOOT).hexdigest()}
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for p in files:
            content = p.read_bytes()
            if p.suffix == ".html":
                if b"<head>" not in content:
                    raise ValueError(f"Cannot safely insert the offline bootstrap in {p.name}")
                content = content.replace(b"<head>", b"<head>" + BOOT_TAG.encode(), 1)
            archive.writestr(p.relative_to(public).as_posix(), content)
        archive.writestr(BOOT_NAME, BOOT)
        archive.writestr("standalone-deployment.json", json.dumps(metadata, indent=2) + "\n")
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("Deployment ZIP integrity failed.")
        if len(archive.infolist()) > 1000 or any(p.file_size > 25 * 1024 * 1024 for p in archive.infolist()):
            raise ValueError("Deployment exceeds Cloudflare's documented dashboard upload limits.")
        for name in required:
            if not name.endswith(".html") and archive.read(name) != (public / name).read_bytes():
                raise ValueError(f"A research/runtime asset changed during packaging: {name}")
    print(json.dumps({"archive": str(output), "file_count": len(files) + 2, "source_revision": revision, "server_api_included": False, "offline_bootstrap": True}))


if __name__ == "__main__":
    main()
