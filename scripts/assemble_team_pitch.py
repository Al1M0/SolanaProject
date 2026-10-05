"""Compose the revised English pitch with native Higgsedit and measured narration.

Usage: python3 scripts/assemble_team_pitch.py narration.mp3 /tmp/team-pitch
Requires ffmpeg, faster-whisper's cached small model and native Higgsedit.
No narration speed change, invented footage or alteration of research results.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path


def run(args):
    subprocess.run([str(x) for x in args], check=True)


def main():
    audio = Path(sys.argv[1]).resolve()
    work = Path(sys.argv[2]).resolve()
    work.mkdir(parents=True, exist_ok=True)
    audio_seconds = float(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(audio)
    ]))
    duration = math.ceil(audio_seconds + 3)
    if duration > 120:
        raise RuntimeError('Narration exceeds the two-minute limit; revise the wording.')
    from faster_whisper import WhisperModel
    models = list(Path('/opt/whisper-models').glob('models--Systran--faster-whisper-small/snapshots/*'))
    if not models:
        raise RuntimeError('A cached ASR model is required to align the actual narration.')
    model = WhisperModel(str(models[0]), device='cpu', compute_type='int8', cpu_threads=4)
    segments, _ = model.transcribe(str(audio), language='en', word_timestamps=True, beam_size=5)
    words, transcript = [], []
    for s in segments:
        transcript.append({'start': s.start, 'end': s.end, 'text': s.text})
        for w in s.words or []:
            token = re.sub('[^a-z]', '', w.word.lower())
            if token:
                words.append({'word': token, 'start': w.start, 'end': w.end})
    (work / 'transcript.json').write_text(json.dumps(transcript, indent=2))
    starts = [0.0]
    for anchor in [('a', 'researcher'), ('in', 'our', 'working'),
                   ('our', 'unchanged', 'synthetic'), ('every', 'attempt'),
                   ('we', 'have', 'retrieved')]:
        found = next((i for i in range(len(words) - len(anchor) + 1)
                      if tuple(w['word'] for w in words[i:i + len(anchor)]) == anchor), None)
        if found is None:
            raise RuntimeError(f'Inspect ASR: paragraph boundary missing: {anchor}')
        starts.append(max(starts[-1], words[found]['start'] - .1))
    if starts != sorted(set(starts)):
        raise RuntimeError('Ambiguous narration order')
    scenes = [
        {'title': 'Solana Quant\nResearch Lab', 'tag': 'THE TEAM', 'lines': [
            'Ali Mukhanbetov', 'Information Systems student at KBTU',
            'Mukhametkali Merey', 'Exploring Python and quantitative trading',
            'A tool we would use to test our own ideas.']},
        {'title': 'Would you follow\nthese wallets?', 'tag': 'THE QUESTION', 'lines': [
            'Wallet activity starts a hypothesis.',
            'Does it beat a comparable baseline',
            'after fees and delays on a separate period?',
            'Initial user: an independent Solana researcher.']},
        {'title': 'Turn the hypothesis\ninto an audit.', 'tag': 'WORKING MVP', 'lines': [
            'Select wallets & tokens · inspect data quality',
            'Training → freeze → historical holdout',
            'Buy-and-hold + fixed momentum',
            'Same engine, dates, capital, universe and costs.']},
        {'title': 'Costs erase the\nobserved gain.', 'tag': 'SYNTHETIC · UNCHANGED SEED 33', 'lines': [
            'Rejecting a weak hypothesis is useful.',
            'Different exposure and turnover remain visible.',
            'Small sample. No proven alpha.'], 'results': [
                ['Wallet gross', '+1.28%', '32 trades', '#8befc4'],
                ['Wallet net', '−1.92%', '32 trades', '#ff969f'],
                ['Buy-and-hold net', '+4.24%', '4 trades', '#8befc4'],
                ['Momentum net', '−8.88%', '104 trades', '#ff969f']]},
        {'title': 'Evidence you can\ninspect and rerun.', 'tag': 'REPRODUCIBLE REVIEW', 'lines': [
            'Dataset hash · frozen assumptions · engine',
            'Attempts, results, exclusions and trades',
            'Export → python3.12 reproduce.py',
            'Historical data may already be known to the user.']},
        {'title': 'Real observations.\nClear remaining gaps.', 'tag': 'CURRENT STATUS', 'lines': [
            'Solana transactions + historical prices retrieved',
            'Five sells matched independent RPC records',
            'REAL performance blocked: prices & exit liquidity',
            'Next: complete study · test with five researchers',
            'Customer demand and pricing remain unvalidated.']},
    ]
    for i, scene in enumerate(scenes):
        scene['at'] = starts[i]
        scene['dur'] = (starts[i + 1] if i < 5 else duration) - starts[i]
    script = '''export default async ({project, rect, text}) => {
      const p = await project({dir:WORK+"/higgsedit",size:"1280x720",fps:24,background:"#080f1c"});
      const txt = (s,x,y,w,h,size=26,color="#edf5f2",extra={}) => text(s,{x,y,width:w,height:h,fontFamily:"DejaVu Sans",fontSize:size,color,...extra});
      const enter = [{property:"opacity",from:0,to:1,at:0,duration:.35},{property:"offsetY",from:18,to:0,at:0,duration:.4}];
      for (const [i,s] of SCENES.entries()) {
        const n = [
          rect({x:0,y:0,width:1280,height:720,fill:{kind:"linear",angle:20,stops:[{offset:0,color:"#071523"},{offset:1,color:"#21183b"}]}}),
          rect({x:62,y:65,width:54,height:4,fill:"#8befc4",radius:2}),
          txt("QUANTLAB  /  COLOSSEUM 2026",130,57,960,30,18,"#b8cdd6"),
          txt(s.tag,62,112,1150,32,18,"#8befc4"),
          txt(s.title,58,165,1155,146,52,"#edf5f2",{fontWeight:700,animate:enter}),
          txt("RESEARCH PROTOTYPE  ·  ENGLISH AI NARRATION",62,668,1000,25,14,"#a5b6c5"),
          txt(String(i+1).padStart(2,"0")+" / 06",1115,666,120,30,16,"#8befc4"),
          rect({x:62,y:643,width:1156,height:2,fill:"#314256"})
        ];
        if (s.results) {
          for (const [j,r] of s.results.entries()) {
            const x = 62+j*291;
            n.push(rect({x,y:329,width:273,height:159,fill:"#102334",radius:12}));
            n.push(txt(r[0],x+15,345,247,35,19,"#b8cdd6"));
            n.push(txt(r[1],x+15,393,247,52,38,r[3],{fontWeight:700}));
            n.push(txt(r[2],x+15,452,247,28,17,"#a5b6c5"));
          }
          s.lines.forEach((l,j)=>n.push(txt(l,64,516+j*36,1150,34,23,j===2?"#ffcf93":"#edf5f2")));
        } else {
          s.lines.forEach((l,j)=>n.push(txt(l,64,337+j*48,1150,45,(i===0&&(j===0||j===2))?29:24,(i===0&&(j===0||j===2))?"#8befc4":"#dce8ed",{animate:[{property:"opacity",from:0,to:1,at:.1+j*.05,duration:.3}]})));
        }
        p.compose(n,{at:s.at,dur:s.dur,name:s.tag});
      }
      const a = await p.add(AUDIO);
      p.cut(a,{from:0,dur:AUDIO_SECONDS,at:0});
      for (const [i,s] of SCENES.entries()) await p.frame(s.at+Math.min(3,s.dur/2),WORK+"/native-"+i+".png");
      if (Math.abs(p.duration()-DURATION)>.06) throw new Error("Unexpected duration");
      await p.render(WORK+"/pitch.mp4",{depth:8,accel:"cpu",bitrate:2400000,shards:3,concurrency:3});
    };'''
    for key, value in {'WORK': str(work), 'SCENES': scenes, 'AUDIO': str(audio),
                       'AUDIO_SECONDS': audio_seconds, 'DURATION': duration}.items():
        script = re.sub(r'\b' + key + r'\b', lambda _: json.dumps(value), script)
    (work / 'edit.js').write_text(script)
    run(['higgsedit', 'build', work / 'edit.js'])
    movie = work / 'pitch.mp4'
    run(['ffmpeg', '-v', 'error', '-i', movie, '-f', 'null', '-'])
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
        'format=duration:stream=codec_name,codec_type,width,height', '-of', 'json', str(movie)]))
    if abs(float(probe['format']['duration']) - duration) > .06:
        raise RuntimeError('Final encoded duration differs')
    from PIL import Image
    sheet = Image.new('RGB', (1280, 1080), '#080f1c')
    for i,s in enumerate(scenes):
        out = work / f'final-{i}.jpg'
        run(['ffmpeg', '-v', 'error', '-ss', s['at'] + min(3,s['dur']/2), '-i', movie,
             '-frames:v', '1', '-q:v', '4', '-y', out])
        img = Image.open(out).convert('RGB').resize((640,360))
        sheet.paste(img,((i%2)*640,(i//2)*360))
    sheet.save(work / 'review.jpg', quality=85)
    summary = {'duration_seconds': float(probe['format']['duration']),
        'narration_seconds': audio_seconds, 'bytes': movie.stat().st_size,
        'sha256': hashlib.sha256(movie.read_bytes()).hexdigest(), 'streams': probe['streams'],
        'audio_sha256': hashlib.sha256(audio.read_bytes()).hexdigest(),
        'scene_starts': starts, 'source': 'AI narrator, native explanatory graphics',
        'narration_time_stretch': False, 'asr_transcript': transcript}
    (work / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
