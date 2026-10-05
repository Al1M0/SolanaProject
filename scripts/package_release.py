"""Package source and the prebuilt offline demo, excluding dependencies and secrets."""
import argparse
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", "node_modules", ".next", "dist", ".sites-runtime", "__pycache__", ".pytest_cache", "artifacts", "out"}


def eligible(path):
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED for part in relative.parts):
        return False
    if path.name.startswith(".env") and path.name != ".env.example":
        return False
    return path.suffix not in {".pyc", ".db", ".db-shm", ".db-wal", ".tsbuildinfo", ".zip", ".gz"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    demo = ROOT / "frontend/out"
    required = [demo / "index.html", demo / "audit/index.html", demo / "research-worker.js", demo / "runtime/pyodide.asm.wasm", demo / "research/engine.py", demo / "research/experiments.py"]
    if not all(path.is_file() for path in required):
        parser.error("Build the browser demo first with npm run build.")
    files = set()
    for directory, folders, filenames in os.walk(ROOT, followlinks=False):
        parent = Path(directory)
        folders[:] = [name for name in folders if name not in EXCLUDED and parent / name not in {ROOT / "frontend/public/runtime", ROOT / "frontend/public/research"}]
        for filename in filenames:
            path = parent / filename
            if not path.is_symlink() and eligible(path):
                files.add(path)
    files.update(path for path in demo.rglob("*") if path.is_file() and not path.is_symlink())
    # Include the inspected research export; arbitrary local ZIPs remain excluded.
    reference_bundle = ROOT / "research/reference/reproduction.zip"
    if reference_bundle.is_file():
        files.add(reference_bundle)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            archive.write(path, "solana-quant-research-lab/" + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Release archive failed its integrity check.")
    print(f"Packaged {len(files)} files: {output}")


if __name__ == "__main__":
    main()
