"""Original disk-backed preparation with portable tool and temp locations."""
import hashlib
import json
import logging
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

import imageio_ffmpeg
import numpy as np
import torch
import folder_paths

log = logging.getLogger(__name__)
FF = shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe()
_probe_name = 'ffprobe.exe' if Path(FF).suffix.lower() == '.exe' else 'ffprobe'
_probe_sibling = Path(FF).with_name(_probe_name)
PROBE = shutil.which('ffprobe') or (str(_probe_sibling) if _probe_sibling.is_file() else 'ffprobe')

def job_key(graph):
    # ComfyUI injects transient is_changed fingerprints during execution.
    graph={k:{'class_type':v.get('class_type'),'inputs':json.loads(json.dumps(v.get('inputs',{})))} for k,v in graph.items()}
    for node in graph.values():
        node.get('inputs',{}).pop('recovery_directory',None)
    return hashlib.sha256(json.dumps(graph,sort_keys=True).encode()).hexdigest()

def atomic_json(path,data):
    path=Path(path);tmp=path.with_suffix('.pending.json')
    tmp.write_text(json.dumps(data,indent=2));tmp.replace(path)

def run(args):
    try:
        p = subprocess.run(args, capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except FileNotFoundError as error:
        raise RuntimeError('Install FFmpeg and ffprobe on PATH, then restart ComfyUI. Both tools are needed to prepare a source video.') from error
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors='replace')[-3000:])
    return p.stdout

def probe(path):
    return json.loads(run([PROBE, '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', str(path)]))

def read_window(source, start, count):
    w,h = source['width'],source['height']
    raw = run([FF,'-v','error','-threads','2','-ss',str(start/24),'-i',source['path'],
               '-frames:v',str(count),'-f','rawvideo','-pix_fmt','rgb24','-threads','2','pipe:1'])
    if len(raw) != count*h*w*3:
        raise RuntimeError('Streaming decoder returned an incomplete section')
    return torch.from_numpy(np.frombuffer(raw,dtype=np.uint8).reshape(count,h,w,3).copy()).float().div_(255)

class H3StreamPrepare:
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # A cached directory can contain output made with a different downstream
        # seed/prompt/reference. Reevaluate to allocate a fresh job directory or
        # validate the full graph against explicitly requested recovery settings.
        return float('nan')

    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{'video':('VIDEO',),'target_megapixels':('FLOAT',{'default':.8,'min':.05,'max':2,'step':.05}),
                            'max_seconds':('FLOAT',{'default':0,'min':0,'max':600,'step':1})},
                'optional':{'recovery_directory':('STRING',{'default':''})},'hidden':{'prompt':'PROMPT'}}
    RETURN_TYPES=('H3_DISK_SOURCE','H3_AUDIO_SOURCE')
    RETURN_NAMES=('frames_24fps','original_audio')
    FUNCTION='prepare'
    CATEGORY='MiniMax Safe'
    def prepare(self,video,target_megapixels,max_seconds,recovery_directory='',prompt=None):
        src=video.get_stream_source()
        if not isinstance(src,(str,Path)):
            raise ValueError('Low-RAM workflow requires a video file from Load Video')
        if getattr(video,'_VideoFromFile__crop',None):
            raise ValueError('Use an uncropped Load Video input for the low-RAM workflow')
        start,duration=video.get_active_trim_window()
        if max_seconds>0:duration=min(duration,max_seconds) if duration else max_seconds
        identity={'job_key':job_key(prompt or {}),'source_size':Path(src).stat().st_size,'source_mtime_ns':Path(src).stat().st_mtime_ns}
        if recovery_directory.strip():
            directory=Path(recovery_directory).resolve()
            saved=json.loads((directory/'recovery.json').read_text())
            if saved['identity']!=identity:raise ValueError('Recovery settings or source file changed; use the original inputs to resume.')
            source=saved['source'];source['directory']=str(directory);source['path']=str(directory/'source.mkv')
            if not Path(source['path']).is_file():raise ValueError('Recovery source is missing')
            log.info('[H3 Recovery] Reusing disk source and completed sections from %s',directory)
            return source,saved['audio']
        w,h=video.get_dimensions()
        scale=math.sqrt(target_megapixels*1000000/(w*h))
        w,h=max(32,round(w*scale/32)*32),max(32,round(h*scale/32)*32)
        recovery_root=Path(folder_paths.get_temp_directory())/'h3_studio_prepare'
        recovery_root.mkdir(parents=True, exist_ok=True)
        directory=Path(tempfile.mkdtemp(prefix='h3_stream_',dir=recovery_root))
        target=directory/'source.mkv'
        args=[FF,'-v','error','-y','-threads','2','-ss',str(start),'-i',str(src)]
        if duration:args+=['-t',str(duration)]
        args+=['-map','0:v:0','-an','-vf',f'fps=24,scale={w}:{h}:flags=bicubic,setsar=1',
               '-c:v','ffv1','-level','3','-threads','2',str(target)]
        run(args)
        stream=next(s for s in probe(target)['streams'] if s['codec_type']=='video')
        length=int(stream['nb_read_frames'])
        if length<1:raise ValueError('Input video has no frames')
        log.info('[H3 Stream] Disk-backed input: %s frames, %sx%s. No full-video tensor.',length,w,h)
        source={'path':str(target),'directory':str(directory),'width':w,'height':h,'length':length}
        audio={'path':str(src),'start':start,'duration':length/24}
        atomic_json(directory/'recovery.json',{'identity':identity,'source':source,'audio':audio})
        return source,audio
