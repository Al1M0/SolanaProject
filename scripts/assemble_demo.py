"""Assemble an honest three-minute product demo from record_demo.cjs output.

Requires ffmpeg, Pillow, faster-whisper's locally cached small model and Higgsedit.
The completed fresh export and its rerun must succeed before rendering.
Only the final MP4 is intended for upload; intermediate study files remain local.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def run(command):
    subprocess.run([str(x) for x in command], check=True)


def speech_sections(audio: Path, work: Path):
    from faster_whisper import WhisperModel
    caches = list(Path('/opt/whisper-models').glob('models--Systran--faster-whisper-small/snapshots/*'))
    if not caches:
        raise RuntimeError('A local small ASR model is required to check narration edit boundaries.')
    model = WhisperModel(str(caches[0]), device='cpu', compute_type='int8', cpu_threads=4)
    segments, info = model.transcribe(str(audio), language='en', word_timestamps=True, beam_size=5)
    words = []
    transcript = []
    for segment in segments:
        transcript.append({'start': segment.start, 'end': segment.end, 'text': segment.text})
        for word in segment.words or []:
            token = re.sub(r'[^a-z]', '', word.word.lower())
            if token:
                words.append({'word': token, 'start': word.start, 'end': word.end})
    (work / 'narration-transcript.json').write_text(json.dumps(transcript, indent=2))
    patterns = [('a', 'solana', 'researcher'), ('solana', 'quant', 'research'), ('we', 'show', 'costs'), ('every', 'attempt', 'stays'), ('we', 'have', 'retrieved')]
    positions = []
    for paragraph, pattern in enumerate(patterns):
        found = next((i for i in range(len(words) - len(pattern) + 1) if tuple(x['word'] for x in words[i:i + len(pattern)]) == pattern), None)
        if found is None and paragraph == 1:
            found = next((max(0, i - 4) for i in range(len(words) - 2) if tuple(x['word'] for x in words[i:i + 3]) == ('turns', 'that', 'question')), None)
        if found is None:
            raise RuntimeError(f'ASR could not locate paragraph {paragraph + 1}; inspect narration-transcript.json before editing.')
        positions.append(found)
    if positions != sorted(set(positions)):
        raise RuntimeError('Narration paragraph order is ambiguous.')
    duration = float(json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)]))['format']['duration'])
    cuts = []
    for n, pos in enumerate(positions):
        start = 0.0 if n == 0 else max(0.0, words[pos]['start'] - .10)
        last = positions[n + 1] - 1 if n < 4 else len(words) - 1
        stop = min(duration, words[last]['end'] + .18)
        if n < 4:
            stop = min(stop, words[positions[n + 1]]['start'] - .06)
        cuts.append((start, stop))
    print(json.dumps({'asr_sections': cuts}), flush=True)
    return cuts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('work', type=Path)
    parser.add_argument('audio', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    work = args.work.resolve()
    meta = json.loads((work / 'recording.json').read_text())
    assert meta.get('complete') and meta.get('reference_values_visible'), 'The actual browser workflow must complete with the unchanged reference.'
    assert meta.get('download_bytes', 0) > 0 and meta.get('reproduction', {}).get('reproduced') is True, 'The fresh browser download must independently reproduce.'
    raw = Path(meta['raw_video'])
    stages = meta['stages']
    ff = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error']
    segments = []

    def footage(start, stop, duration, title, wait=False):
        begin, end = stages[start], stages[stop]
        assert end > begin
        number = len(segments)
        output = work / f'cut-{number:02d}.mp4'
        ratio = duration / (end - begin)
        if wait and end - begin > 4:
            filters = f'[0:v]split[a][b];[a]trim=start={begin}:end={begin + 1.5},setpts=PTS-STARTPTS[a1];[b]trim=start={end - 1.5}:end={end},setpts=PTS-STARTPTS[b1];[a1][b1]concat=n=2:v=1:a=0,setpts={duration / 3}*PTS,fps=24,tpad=stop_mode=clone:stop_duration=1[v]'
            opts = ['-filter_complex', filters, '-map', '[v]']
        else:
            opts = ['-vf', f'trim=start={begin}:end={end},setpts={ratio}*(PTS-STARTPTS),fps=24,tpad=stop_mode=clone:stop_duration=1']
        run(ff + ['-i', raw] + opts + ['-t', duration, '-c:v', 'libx264', '-crf', '22', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-an', output])
        segments.append({'path': str(output), 'duration': duration, 'caption': title, 'wait_shortened': wait})

    footage('intro', 'setup', 20, '01 / THE QUESTION: Does this wallet hypothesis beat a baseline after costs?')
    card = Image.new('RGB', (1280, 650), '#10191f')
    d = ImageDraw.Draw(card)
    font_dir = Path('/usr/share/fonts/truetype/dejavu')
    def label(xy, content, size=26, color='#edf5f2', bold=False):
        f = font_dir / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
        d.text(xy, content, font=ImageFont.truetype(str(f), size), fill=color)
    label((60, 76), 'REAL INGESTION / CURRENT RESEARCH STATUS', 19, '#8befc4', True)
    label((60, 133), 'Genuine ingestion. Clear evidence limits.', 40, bold=True)
    for n, line in enumerate(['Solana transactions and historical prices retrieved.', 'Five deterministic sells matched independent RPC records.', 'Required prices remain incomplete.', 'Historical exit liquidity unavailable: REAL performance blocked.']):
        label((65, 240 + n * 64), line, 25)
    label((65, 545), 'Status from committed research evidence; this is an explanatory card.', 20, '#b1c3c5')
    label((65, 583), 'The recorded end-to-end workflow uses unchanged SYNTHETIC seed 33.', 20, '#8befc4')
    card.save(work / 'real-status.png')
    real_clip = work / 'real-status.mp4'
    run(ff + ['-loop', '1', '-framerate', '24', '-i', work / 'real-status.png', '-t', '30', '-c:v', 'libx264', '-crf', '22', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-an', real_clip])
    segments.append({'path': str(real_clip), 'duration': 30, 'caption': '02 / REAL STATUS: reported ingestion evidence; complete real performance is blocked.'})
    footage('setup', 'training_start', 18, '03 / SETUP: unchanged tokens, capital, fees, delay and chronological split.')
    footage('training_start', 'training_result', 4, '04 / TRAINING: actual computation; waiting time shortened.', True)
    footage('training_result', 'freeze_start', 19, '04 / TRAINING: seven pre-specified rows; no holdout tuning.')
    footage('freeze_start', 'holdout_start', 17, '05 / FREEZE: immutable manifest; this offline lock stays on this device.')
    footage('holdout_start', 'holdout_result', 3, '06 / HOLDOUT: actual later-period computation; waiting time shortened.', True)
    footage('holdout_result', 'trade', 29, '06 / HOLDOUT: wallet +1.28% gross / -1.92% net; buy-and-hold +4.24% net.')
    footage('trade', 'export_start', 16, '07 / TRADE: inspect actual modeled timing, gross result and cost components.')
    footage('export_start', 'export_complete', 3, '08 / EXPORT: actual verification and download; waiting time shortened.', True)
    footage('export_complete', 'reproduction_proof', 4, '08 / EXPORT: fresh reproduction ZIP downloaded successfully.')
    footage('reproduction_proof', 'end', 17, '09 / VERIFY: actual Python rerun of this fresh export returned reproduced: true.')
    assert sum(s['duration'] for s in segments) == 180
    (work / 'edit-segments.json').write_text(json.dumps(segments, indent=2))
    script = '''export default async ({ project, rect, text }) => {
      const p = await project({dir:PROJECT_DIR, size:"1280x720",fps:24,background:"#0c1217"});
      const clips = SEGMENTS;
      let at = 0;
      for (const c of clips) {
        const h = await p.add(c.path);
        p.cut(h, {from:0,dur:c.duration,at,fit:"contain"});
        p.compose([
          rect({x:0,y:0,width:1280,height:35,fill:"#0c1217"}),
          text("SOLANA QUANT  |  SYNTHETIC  |  RECORDED PUBLIC MVP  |  EDITED TIMING", {x:24,y:8,width:1232,height:23,fontFamily:"DejaVu Sans",fontSize:15,color:"#8befc4"}),
          rect({x:0,y:685,width:1280,height:35,fill:"#0c1217"}),
          text(c.caption,{x:24,y:692,width:1232,height:22,fontFamily:"DejaVu Sans",fontSize:17,color:"#edf5f2"})
        ],{at,dur:c.duration,name:c.caption.slice(0,24)});
        at += c.duration;
      }
      if (Math.abs(p.duration()-180) > .05) throw new Error("Unexpected timeline duration");
      for (const t of [7,34,60,82,98,127,147,173]) await p.frame(t, FRAME_DIR+"/native-"+t+".png");
      await p.render(VIDEO_OUT,{depth:8,accel:"cpu",bitrate:3000000,shards:3,concurrency:3});
    };'''
    values = {'PROJECT_DIR': str(work / 'higgsedit'), 'SEGMENTS': segments, 'FRAME_DIR': str(work), 'VIDEO_OUT': str(work / 'picture-native.mp4')}
    for key, value in values.items():
        script = script.replace(key, json.dumps(value))
    (work / 'edit.js').write_text(script)
    run(['higgsedit', 'build', work / 'edit.js'])
    cuts = speech_sections(args.audio, work)
    # Original narration paragraphs: question, workflow, costs, reproduction, real status.
    placements = [(0, 0), (4, 21), (1, 51), (2, 109), (3, 156)]
    filters = []
    for n, (paragraph, at) in enumerate(placements):
        start, stop = cuts[paragraph]
        limit = 180 - at
        duration = (stop - start) / .85
        if duration > limit:
            raise RuntimeError('Narration exceeds its final scene.')
        filters.append(f'[1:a]atrim=start={start}:end={stop},asetpts=PTS-STARTPTS,atempo=0.85,adelay={at * 1000}|{at * 1000}[s{n}]')
    filters.append('[s0][s1][s2][s3][s4]amix=inputs=5:normalize=0,apad[a]')
    # CRF encoding keeps the mostly static UI readable with a small sharing file.
    run(ff + ['-i', work / 'picture-native.mp4', '-i', args.audio, '-filter_complex', ';'.join(filters), '-map', '0:v:0', '-map', '[a]', '-c:v', 'libx264', '-crf', '22', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-t', '180', '-movflags', '+faststart', args.output])
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_name,codec_type,width,height', '-of', 'json', str(args.output)]))
    assert abs(float(probe['format']['duration']) - 180) < .05
    run(ff + ['-i', args.output, '-f', 'null', '-'])
    for t in [7,34,60,82,98,127,147,173]:
        run(ff + ['-ss', t, '-i', args.output, '-frames:v', '1', '-q:v', '4', work / f'final-{t}.jpg'])
    summary = {'duration_seconds': float(probe['format']['duration']), 'bytes': args.output.stat().st_size, 'streams': probe['streams'], 'fresh_export_reproduced': True, 'scene_seconds': [0,20,50,68,91,108,140,156,163], 'narration_sections': cuts}
    (work / 'final-video-summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
