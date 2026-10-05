"""Compose the supplied narration into a pitch MP4. Requires Pillow and ffmpeg.

Usage: python3 scripts/render_pitch.py --work-dir /tmp/solana-pitch
The default output is exactly two minutes, using the supplied narration at a
calmer tempo without changing its pitch. The original MP3 remains unchanged.
The five visual sections are explanatory slides, not a product-demo recording.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "docs/submission/media"
W, H, FPS = 1280, 720, 24
BG = (12, 18, 23)
WHITE = "#EDF5F2"
MUTED = "#AEC0C0"
MINT = "#78E7BE"
PURPLE = "#B69EF8"
RED = "#F3A5AE"
FONT_ROOT = Path("/usr/share/fonts/truetype/dejavu")


def font(size: int, bold: bool = False):
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = FONT_ROOT / filename
    return ImageFont.truetype(str(path if path.exists() else filename), size)


def text(draw, xy, value, size=24, color=WHITE, bold=False):
    draw.text(xy, value, font=font(size, bold), fill=color)


def lines(draw, xy, values, size=28, gap=43, color=MUTED, bold=False):
    for n, value in enumerate(values):
        text(draw, (xy[0], xy[1] + n * gap), value, size, color, bold)


def card(draw, rect, outline="#344247", fill="#152126"):
    draw.rounded_rectangle(rect, radius=20, fill=fill, outline=outline, width=2)


def base(section, number):
    image = Image.new("RGB", (W, H), BG)
    pixels = image.load()
    for y in range(H):
        for x in range(W):
            teal = max(0, 1 - math.hypot((x - 100) / 1100, (y - 30) / 750))
            violet = max(0, 1 - math.hypot((x - 1200) / 1100, (y - 600) / 850))
            pixels[x, y] = (int(12 + 9 * violet), int(18 + 15 * teal), int(23 + 10 * teal + 14 * violet))
    draw = ImageDraw.Draw(image)
    for n, col in enumerate([MINT, PURPLE, MINT]):
        draw.polygon([(62 + n * 4, 42 + n * 12), (98 + n * 4, 42 + n * 12), (92 + n * 4, 49 + n * 12), (56 + n * 4, 49 + n * 12)], fill=col)
    text(draw, (122, 40), "SOLANA QUANT", 22, WHITE, True)
    text(draw, (122, 70), "Research Lab", 18, MUTED)
    text(draw, (1075, 55), f"{number:02d} / 05", 18, MUTED)
    text(draw, (62, 126), section.upper(), 18, MINT, True)
    draw.line((62, 649, 1218, 649), fill="#304043", width=1)
    text(draw, (62, 670), "solana-quant.hkakasi358.workers.dev", 19, MUTED)
    text(draw, (997, 670), "ENGLISH PITCH", 17, MUTED)
    return image, draw


def make_slides(work):
    image, d = base("The research question", 1)
    lines(d, (62, 187), ["Several wallets buy.", "Should you follow?"], 58, 79, WHITE, True)
    lines(d, (65, 376), ["Wallet activity is a hypothesis.", "Test it after fees and delays", "on a separate evaluation period."], 29, 45)
    card(d, (905, 208, 1218, 566), "#466B65")
    text(d, (935, 237), "THE QUESTION", 18, MINT, True)
    lines(d, (935, 302), ["Does the signal", "beat a simple", "baseline?"], 28, 45, WHITE, True)
    text(d, (935, 496), "Costs included.", 22, MINT)
    image.save(work / "slide-1.png")

    image, d = base("One auditable workflow", 2)
    text(d, (62, 180), "Turn a hypothesis into evidence.", 44, WHITE, True)
    stages = [("01", "Inspect data", "Wallets, tokens, coverage"), ("02", "Train", "Compare assumptions"), ("03", "Freeze", "Save the configuration"), ("04", "Holdout", "Evaluate a later period")]
    for n, (num, title, sub) in enumerate(stages):
        x = 62 + (n % 2) * 587
        y = 291 + (n // 2) * 148
        card(d, (x, y, x + 565, y + 128))
        text(d, (x + 24, y + 24), num, 22, PURPLE, True)
        text(d, (x + 89, y + 21), title, 28, WHITE, True)
        text(d, (x + 89, y + 68), sub, 21, MUTED)
    text(d, (64, 605), "Wallet hypothesis  ·  Buy-and-hold  ·  Fixed momentum  ·  Same engine", 21, MINT)
    image.save(work / "slide-2.png")

    image, d = base("Untuned synthetic demonstration", 3)
    text(d, (62, 180), "Costs erase the observed gain.", 46, WHITE, True)
    for n, (label, value, detail, color) in enumerate([
        ("WALLET · BEFORE COSTS", "+1.28%", "Gross return", MINT),
        ("WALLET · AFTER COSTS", "−1.92%", "$319.68 modeled costs", RED),
        ("BUY-AND-HOLD · NET", "+4.24%", "Same evaluation period", PURPLE),
    ]):
        x = 62 + n * 392
        card(d, (x, 290, x + 369, 506))
        text(d, (x + 22, 316), label, 17, MUTED, True)
        text(d, (x + 22, 365), value, 57, color, True)
        text(d, (x + 22, 455), detail, 20, MUTED)
    text(d, (65, 552), "Rejecting a weak hypothesis is a useful research outcome.", 27, WHITE)
    text(d, (65, 601), "SYNTHETIC observations  ·  Modeled costs  ·  No claim of real profitability", 20, MINT)
    image.save(work / "slide-3.png")

    image, d = base("Evidence another researcher can rerun", 4)
    text(d, (62, 180), "Keep the experiment. Export the proof.", 42, WHITE, True)
    card(d, (62, 284, 742, 578))
    lines(d, (92, 317), ["Frozen configuration + data fingerprint", "Exact execution-engine source", "Results, trades and cost assumptions", "Credential-free reproduction ZIP"], 24, 57, WHITE)
    card(d, (770, 284, 1218, 578), "#655783")
    text(d, (801, 319), "REPRODUCE", 22, PURPLE, True)
    text(d, (801, 394), "python3 reproduce.py", 23, WHITE, True)
    lines(d, (801, 461), ["Every attempt stays visible.", "Check the evidence yourself."], 21, 43)
    text(d, (65, 609), "A historical lock does not prove an unseen holdout or profitable alpha.", 21, MUTED)
    image.save(work / "slide-4.png")

    image, d = base("Current status and next steps", 5)
    text(d, (62, 180), "Working audit. Clear remaining gaps.", 43, WHITE, True)
    card(d, (62, 285, 628, 588), "#466B65")
    text(d, (91, 314), "BUILT & CHECKED", 21, MINT, True)
    lines(d, (91, 369), ["Synthetic audit and benchmarks", "Frozen attempts and export", "Genuine transaction ingestion", "Five sells checked against RPC"], 22, 48, WHITE)
    card(d, (650, 285, 1218, 588), "#655783")
    text(d, (679, 314), "NEXT", 21, PURPLE, True)
    lines(d, (679, 369), ["Complete historical price coverage", "Obtain historical exit liquidity", "Finish the genuine performance study", "Test with five researchers"], 21, 48, WHITE)
    text(d, (65, 609), "Real performance is blocked. Customer demand and pricing remain unvalidated.", 20, MUTED)
    image.save(work / "slide-5.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--duration-seconds", type=float, default=120.0)
    args = parser.parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    make_slides(args.work_dir)
    audio = MEDIA / "pitch-audio.mp3"
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(audio)]))
    original_duration = float(probe["format"]["duration"])
    end = round(args.duration_seconds * FPS) / FPS
    speech_duration = end - 1.5
    tempo = original_duration / speech_duration if speech_duration > 0 else 0
    if not 0.5 <= tempo <= 2.0:
        parser.error("Requested duration needs a narration tempo outside 0.5–2.0.")
    scale = speech_duration / original_duration
    boundaries = [round(t * scale * FPS) / FPS for t in [0, 14.9, 33.2, 53.5, 69.9]] + [end]
    if any(stop <= start for start, stop in zip(boundaries, boundaries[1:])):
        parser.error("Requested duration is too short for the five sections.")
    segments = []
    for n, (start, stop) in enumerate(zip(boundaries, boundaries[1:]), 1):
        duration = round((stop - start) * FPS) / FPS
        segment = args.work_dir / f"segment-{n}.mp4"
        filt = f"zoompan=z='min(pzoom+0.000012,1.008)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps={FPS},fade=t=in:st=0:d=0.25,fade=t=out:st={max(0,duration-0.25)}:d=0.25"
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(args.work_dir / f"slide-{n}.png"), "-t", str(duration), "-vf", filt, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-an", str(segment)], check=True)
        segments.append(segment)
        print(f"Rendered section {n}/5", flush=True)
    concat = args.work_dir / "concat.txt"
    concat.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in segments))
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-af", f"atempo={tempo:.10f},apad", "-t", str(end), "-movflags", "+faststart", str(MEDIA / "pitch.mp4")], check=True)
    print(json.dumps({"pitch": str(MEDIA / "pitch.mp4"), "target_duration_seconds": end, "narration_tempo": tempo, "bytes": (MEDIA / "pitch.mp4").stat().st_size}), flush=True)


if __name__ == "__main__":
    main()
