"""Asset-free, native Settings using the Explorer's existing design system."""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import media
from modern_ui import BG,SURFACE,INK,MUTED,ACCENT,Button,Navigation,Section

def build(a):
 w=a.settings_window=tk.Toplevel(a.root);w.withdraw();w.title('ORC · '+a.tr('Configurações'))
 w.geometry('720x650');w.minsize(620,480);w.configure(bg=BG);w.transient(a.root)
 w.protocol('WM_DELETE_WINDOW',w.withdraw);w._translate=a.tr
 a.style.configure('SettingsCard.TFrame',background=SURFACE)
 for name,base in [('SettingsCard.TLabel',INK),('SettingsMuted.TLabel',MUTED),('SettingsHeading.TLabel',INK)]:
  a.style.configure(name,background=SURFACE,foreground=base,font=('Segoe UI',-13,'bold') if name=='SettingsHeading.TLabel' else ('Segoe UI',-12))
 body=ttk.Frame(w,padding=(24,20));body.pack(fill='both',expand=True)
 ttk.Label(body,text='Configurações',style='Title.TLabel').pack(anchor='w')
 ttk.Label(body,text='Ferramentas de mídia e informações do aplicativo',style='Muted.TLabel').pack(anchor='w',pady=(4,16))
 a.inspector_tabs=Navigation(body);a.inspector_tabs.pack(fill='x',pady=(0,16))
 pages=ttk.Frame(body);pages.pack(fill='both',expand=True)
 a.settings_information=ctk.CTkScrollableFrame(pages,fg_color=BG,corner_radius=0,scrollbar_button_color='#45484e')
 a.dependency_panel=ctk.CTkScrollableFrame(pages,fg_color=BG,corner_radius=0,scrollbar_button_color='#45484e')
 for page,title in [(a.settings_information,'Informações'),(a.dependency_panel,'Dependências')]:a.inspector_tabs.add(page,text=title)
 # Stable Section compatibility for existing localized shell/tests; no old chrome.
 a.sections['Dependências']=Section(a.dependency_panel,'Dependências')
 a.dependency_links={'ffmpeg_download':'https://ffmpeg.org/download.html','ffmpeg_repo':'https://github.com/FFmpeg/FFmpeg','ffmpeg_windows':'https://www.gyan.dev/ffmpeg/builds/','vgmstream_download':'https://github.com/vgmstream/vgmstream/releases','vgmstream_repo':'https://github.com/vgmstream/vgmstream'}
 def button(parent,text,command,primary=False,width=100):
  b=Button(parent,text,command,primary,width);a.modern_buttons.append(b);a.label_sources[b]=text;return b
 def card(parent):
  f=ttk.Frame(parent,padding=16,style='SettingsCard.TFrame');f.pack(fill='x',pady=(0,12));return f
 def label(parent,text,style='SettingsMuted.TLabel'):
  l=ttk.Label(parent,text=text,style=style,wraplength=580);l.pack(fill='x',anchor='w',pady=(0,8))
  parent.bind('<Configure>',lambda e:l.configure(wraplength=max(200,e.width-32)),add='+');return l
 info=card(a.settings_information)
 label(info,'Fontes somente leitura • extração sem sobrescrever','SettingsHeading.TLabel')
 label(info,'GPU OpenGL obrigatória, sem fallback CPU ou shaders originais do jogo.')
 ttk.Label(info,textvariable=a.gpu_info,style='SettingsMuted.TLabel',wraplength=550).pack(fill='x',pady=(0,8))
 limits=card(a.settings_information);label(limits,'Limitações','SettingsHeading.TLabel')
 for text in ['FM6S 17/18 • IM6S não é geometria.','Skeleton em bind pose, sem skinning/animação.','Texturas externas/referências de 4 bytes requerem arquivos completos.','Wwise lista mídia, não simula eventos.','Vídeo: prévia até 10s/12fps sem áudio sincronizado.','SSG ≤ 1 GB • cache ≤ 4 GB.','Não redistribua assets do jogo.']:label(limits,text)
 button(limits,'Limitações / ajuda',lambda:(w.withdraw(),a.help()),width=180).pack(anchor='w')
 a.dep_vars={};a.dependency_cards={};a.dependency_entries={};a.dependency_status={};a.dependency_choose={}
 specs=[('ffmpeg','FFmpeg','FFmpeg: áudio comum e prévia Bink/vídeo. ffprobe: inspeção externa opcional, não usado pelo app.', [('ffmpeg_download','Site oficial'),('ffmpeg_repo','Repositório'),('ffmpeg_windows','Gyan · terceiro')]),('vgmstream','vgmstream-cli','vgmstream: decodificação de mídia Wwise compatível.', [('vgmstream_download','Releases oficiais'),('vgmstream_repo','Repositório')]),('blender','Blender','Blender opcional: FBX, blend e GLB. Extração bruta não requer Blender.', [('blender_download','Site oficial'),('blender_repo','Repositório')])]
 detected=media.dependencies()
 import blender_export
 detected['blender']=blender_export.blender_path()
 a.dependency_links.update({'blender_download':'https://www.blender.org/download/','blender_repo':'https://github.com/blender/blender'})
 for key,title,description,links in specs:
  f=card(a.dependency_panel);a.dependency_cards[key]=f
  label(f,title,'SettingsHeading.TLabel');label(f,description)
  status=a.localized_var(value='Detecção: '+('Detectado' if detected[key] and __import__('pathlib').Path(detected[key]).is_file() else 'Não detectado'))
  a.dependency_status[key]=status;ttk.Label(f,textvariable=status,style='SettingsMuted.TLabel').pack(anchor='w',pady=(0,8))
  r=ttk.Frame(f,style='SettingsCard.TFrame');r.pack(fill='x',pady=(0,8))
  v=tk.StringVar(value=detected[key] or '');a.dep_vars[key]=v
  def update_detection(*args,k=key):
   from pathlib import Path
   path=a.dep_vars[k].get().strip();a.dependency_status[k].set('Detecção: '+('Detectado' if path and Path(path).is_file() else 'Não detectado'))
  v.trace_add('write',update_detection)
  entry=ctk.CTkEntry(r,textvariable=v,height=34,fg_color=BG,border_color='#45484e',border_width=1,text_color=INK,font=('Segoe UI',12))
  entry.pack(side='left',fill='x',expand=True,padx=(0,8));a.dependency_entries[key]=entry
  b=button(r,'Selecionar…',lambda k=key:a.choose_dep(k),width=104);b.configure(fg_color='#36393e');b.pack(side='right');a.dependency_choose[key]=b
  r=ttk.Frame(f,style='SettingsCard.TFrame');r.pack(fill='x')
  for link,text in links:button(r,text,lambda k=link:a.open_dependency_link(k),width=130 if text=='Gyan · terceiro' else 120).pack(side='left',padx=(0,4))
 label(a.dependency_panel,'Dependências opcionais: mídia; GPU OpenGL de hardware é obrigatória e integrada.',style='Muted.TLabel')
 footer=ttk.Frame(body);footer.pack(fill='x',pady=(16,0))
 a.settings_feedback=a.localized_var(value='Use somente executáveis oficiais confiáveis.')
 a.settings_feedback_label=ttk.Label(footer,textvariable=a.settings_feedback,style='Muted.TLabel',wraplength=420);a.settings_feedback_label.pack(side='left',fill='x',expand=True,padx=(0,12))
 a.settings_save=button(footer,'Salvar caminhos',a.save_deps,True,144)
 def select(event=None):
  for page in (a.settings_information,a.dependency_panel):page.pack_forget()
  index=a.inspector_tabs.index('current');(a.settings_information,a.dependency_panel)[index].pack(fill='both',expand=True)
  if index==1:a.settings_save.pack(side='right')
  else:a.settings_save.pack_forget()
 a.inspector_tabs.bind('<<NotebookTabChanged>>',select);select()
