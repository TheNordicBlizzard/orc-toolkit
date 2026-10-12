import tempfile,winsound,wave,threading
from pathlib import Path
import media
class Player:
 def __init__(self):
  scratch=media.home()/'cache';scratch.mkdir(parents=True,exist_ok=True)
  self.temp=tempfile.TemporaryDirectory(prefix='audio_',dir=scratch);self.lock=threading.Lock();self.refresh()
 def refresh(self):
  values=media.dependencies();self.ffmpeg=values['ffmpeg'];self.vgmstream=values['vgmstream']
 def decode(self,asset,cancel=None):
  with self.lock:
   self.stop()
   if asset.size>256*1024**2:raise ValueError('Áudio acima de 256 MB: selecione mídia interna do banco.')
   data=asset.read();ext=Path(asset.name).suffix.lower();src=Path(self.temp.name)/('input'+ext);src.write_bytes(data);dest=Path(self.temp.name)/'preview.wav';dest.unlink(missing_ok=True)
   if ext=='.wav':dest.write_bytes(data)
   elif ext in ('.wem','.bnk','.pck','.ogg','.xma') and self.vgmstream:
    media.run([self.vgmstream,'-i','-o',str(dest),str(src)],cancel)
   elif self.ffmpeg:
    media.run([self.ffmpeg,'-nostdin','-v','error','-y','-i',str(src),'-t','600','-vn','-acodec','pcm_s16le',str(dest)],cancel)
   else:raise ValueError('Configure vgmstream para Wwise ou FFmpeg para áudio comum em Dependências.')
   if cancel is not None and cancel.is_set():raise InterruptedError('Cancelado.')
   try:
    with wave.open(str(dest)) as w:
     if w.getcomptype()!='NONE' or not w.getnframes():raise ValueError('WAV PCM vazio/comprimido.')
     self.last_decode={'frames':w.getnframes(),'rate':w.getframerate(),'channels':w.getnchannels(),'bytes':dest.stat().st_size,'decoder':'vgmstream' if ext=='.wem' else 'FFmpeg/WAV'}
    return dest
   except Exception as e:raise ValueError('Não foi possível reproduzir WAV: '+str(e)) from e
 def play(self,asset,cancel=None):
  dest=self.decode(asset,cancel)
  winsound.PlaySound(str(dest),winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_NODEFAULT)
  return 'Reproduzindo WAV PCM decodificado • '+self.last_decode['decoder']
 def stop(self):winsound.PlaySound(None,0)
 def close(self):self.stop();self.temp.cleanup()

