from pathlib import Path
import sys,json,shutil,subprocess,time,tempfile,os
from PIL import Image

def home():
 if not getattr(sys,'frozen',False):return Path(__file__).resolve().parent
 exe=Path(sys.executable).resolve();local=exe.parent.parent/'asset_explorer'
 return local if exe.parent.name.casefold()=='dist' and local.is_dir() else exe.parent/'ORC_Asset_Explorer_data'

def dependencies():
 config=home()/'dependencies.json'
 try:values=json.loads(config.read_text(encoding='utf-8'))
 except (OSError,ValueError):values={}
 ff=Path.home()/'AppData/Local/hermes/tools/ffmpeg-9.0.1-win32-x64/bin/ffmpeg.exe'
 vg=home()/'dependencies/vgmstream/vgmstream-cli.exe'
 return {'ffmpeg':values.get('ffmpeg') or shutil.which('ffmpeg') or (str(ff) if ff.exists() else None),'vgmstream':values.get('vgmstream') or shutil.which('vgmstream-cli') or (str(vg) if vg.exists() else None)}

def run(command,cancel=None,timeout=90):
 with tempfile.TemporaryFile() as errors:
  proc=subprocess.Popen(command,stdout=errors,stderr=errors,creationflags=subprocess.CREATE_NO_WINDOW);start=time.monotonic()
  while proc.poll() is None:
   if (cancel is not None and cancel.is_set()) or time.monotonic()-start>timeout:
    proc.terminate()
    try:proc.wait(5)
    except subprocess.TimeoutExpired:proc.kill();proc.wait()
    raise InterruptedError('Cancelado.' if cancel is not None and cancel.is_set() else 'Decoder excedeu tempo de segurança.')
   time.sleep(.04)
  if proc.returncode:
   errors.seek(0);text=errors.read(8192).decode('utf-8','replace');raise ValueError('Decoder recusou o arquivo: '+text)

def video_frames(path,seconds=10,start=0,cancel=None):
 ff=dependencies()['ffmpeg']
 if not ff:raise ValueError('Configure FFmpeg na seção Dependências.')
 scratch=home()/'cache';scratch.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='video_',dir=scratch) as temp:
  run([ff,'-nostdin','-v','error','-ss',str(max(0,start)),'-i',str(path),'-t',str(min(10,seconds)),'-an','-vf','fps=12,scale=640:-2','-frames:v','120',str(Path(temp)/'%03d.png')],cancel)
  result=[]
  for p in sorted(Path(temp).glob('*.png')):
   if cancel is not None and cancel.is_set():raise InterruptedError('Cancelado.')
   with Image.open(p) as im:result.append(im.convert('RGB'))
  if not result:raise ValueError('Nenhum quadro de vídeo decodificado.')
  return result
