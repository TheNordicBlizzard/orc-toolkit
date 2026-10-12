import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
import threading,queue,sys,json,tempfile
from PIL import Image,ImageTk
import core,models,media
import i18n,webbrowser
from audio import Player
class Section(ttk.Frame):
 def __init__(self,parent,title,opened=True):
  super().__init__(parent);self.title=title;self.opened=opened
  self.header=ttk.Button(self,command=self.toggle);self.header.pack(fill='x');self.body=ttk.Frame(self,padding=5);self.refresh()
 def refresh(self):
  self.header.configure(text=('▼ ' if self.opened else '▶ ')+getattr(self.winfo_toplevel(),'_translate',lambda s:s)(self.title))
  if self.opened:self.body.pack(fill='x')
  else:self.body.pack_forget()
 def toggle(self):self.opened=not self.opened;self.refresh()
class Explorer:
 def __init__(self,root):
  self.root=root;root.title('ORC Asset Explorer');root.geometry('1360x850');root.minsize(1024,680)
  import editor_style
  self.style=editor_style.apply(root)
  self.language_settings=media.home()/'ui_language.json';self.language='pt-BR'
  try:self.language=json.loads(self.language_settings.read_text(encoding='utf-8')).get('language','pt-BR')
  except (OSError,ValueError):pass
  if self.language not in ('pt-BR','en'):self.language='pt-BR'
  root._translate=self.tr;self.label_sources={};self.localized_vars=[]
  self.assets=[];self.categories=[];self.busy=False;self.events=queue.Queue();self.mesh=None;self.detail=None;self.bones=None;self.photo=None;self.image=None;self.yaw=.4;self.pitch=.1;self.zoom=1;self.texture_zoom=1;self.pan=(0,0);self.camera_pan=(0,0);self.drag=(0,0);self.player=Player();self.closed=False;self.cancel_event=threading.Event();self.buttons=[];self.sections={};self.frames=[];self.video_id=None;self.render_id=None;self.video_index=0
  import modern_ui
  modern_ui.build(self)
  self.build_menu();self.refresh_language()
  import traceback
  root.report_callback_exception=lambda typ,error,tb:self.preview_error(''.join(traceback.format_exception(typ,error,tb)))
  root.update_idletasks()
  if not self.gpu.context_created:
   try:self.gpu.tkMap(None)
   except Exception as e:self.gpu.error=str(e);self.gpu_info.set('GPU obrigatória indisponível: '+str(e))
  self.gpu.place_forget();self.welcome.lift();root.update_idletasks();self.fit_editor_panes()
  for b in self.modern_buttons:self.tooltips.append(editor_style.Tooltip(b,self,self.label_sources.get(b,'')))
 def show_batch_dialog(self):
  import full_export_ui
  return full_export_ui.batch_dialog(self)
 def show_export_dialog(self):
  import full_export_ui
  return full_export_ui.export_dialog(self)
 def show_settings(self):
  self.settings_window.deiconify();self.settings_window.lift()
 def toggle_log(self):
  if self.log_panel.winfo_ismapped():self.log_panel.pack_forget()
  else:self.log_panel.pack(fill='x',before=self.statusbar)
 def open_dependency_link(self,key):return webbrowser.open(self.dependency_links[key])
 def fit_editor_panes(self):
  if self.closed:return
  width=self.editor_pane.winfo_width();compact=width<1180
  self.editor_pane.sashpos(0,216 if compact else 248)
  if len(self.editor_pane.panes())>2:self.editor_pane.sashpos(1,width-(248 if compact else 280))
 def toggle_inspector(self):
  if str(self.inspector) in self.editor_pane.panes():self.editor_pane.forget(self.inspector)
  else:
   self.editor_pane.add(self.inspector,weight=0)
   # Resolve pane geometry before placing sashes (idle can run before map).
   self.root.update_idletasks();self.fit_editor_panes()
 def present_context(self,index):
  import modern_ui
  self.active_context=index;self.context_tabs.select(index)
  modern_ui.inspector_context(self,index)
  if index in (2,4):self.canvas.pack_forget();self.text.pack(fill='both',expand=True,pady=(5,0),before=self.viewport_hint)
  else:self.text.pack_forget();self.canvas.pack(fill='both',expand=True,before=self.viewport_hint)
 def context_changed(self,event=None):
  index=self.context_tabs.index('current')
  if getattr(self,'context_sync',False) or index==getattr(self,'active_context',0):return
  self.active_context=index;self.present_context(index)
  if index==4:self.show_hex();return
  section=self.sections[['Modelos','Texturas','Áudio','Vídeo'][index]]
  if not section.opened:section.toggle()
  self.set_category(['Modelos','Texturas','Áudio','Vídeo'][index])
  candidates=self.tree.get_children()
  first=next((i for i in candidates if index!=1 or self.assets[int(i)].size>128),None)
  if first is not None:self.tree.selection_set(first);self.tree.focus(first);self.tree.see(first)
 def build_menu(self):
  self.open_menu=tk.Menu(self.root,tearoff=False)
  for name,cmd in [('Abrir SSG / BNK / PCK',self.open_ssg),('Abrir pasta',self.open_folder)]:self.open_menu.add_command(label=self.tr(name),command=cmd)
  self.extract_menu=tk.Menu(self.root,tearoff=False)
  for name,cmd in [('Extrair selecionados',lambda:self.extract(False)),('Extrair todos',lambda:self.extract(True)),('Extrair jogo completo…',self.show_batch_dialog),('Exportar modelos (Blender)…',self.show_export_dialog)]:self.extract_menu.add_command(label=self.tr(name),command=cmd)
  self.root.bind('<Control-o>',lambda e:self.open_ssg());self.root.bind('<Control-Shift-O>',lambda e:self.open_folder());self.root.bind('<Escape>',lambda e:self.cancel())
 def tr(self,text):return i18n.translate(text,self.language)
 def localized_var(self,**kwargs):
  v=i18n.LocalizedVar(self,**kwargs);self.localized_vars.append(v);return v
 def refresh_language(self):
  self.language_display.set('English' if self.language=='en' else 'Português (Brasil)')
  headers={s.header for s in list(self.sections.values())+[self.advanced_model,self.manual_section]}
  def visit(widget):
   if widget not in headers and widget.winfo_class() in ('TButton','TLabel','TCheckbutton') and not widget.cget('textvariable'):
    source=self.label_sources.setdefault(widget,str(widget.cget('text')));widget.configure(text=self.tr(source))
   for child in widget.winfo_children():visit(child)
  visit(self.root)
  for b in self.modern_buttons:b.configure(text=self.tr(self.label_sources[b]))
  for section in list(self.sections.values())+[self.advanced_model,self.manual_section]:section.refresh()
  self.search_entry.configure(placeholder_text=self.tr('Pesquisar assets'))
  self.settings_window.title('ORC · '+self.tr('Configurações'))
  self.tree.heading('#0',text=self.tr('2. Selecione um asset (nome)'))
  self.combo['values']=[self.tr(s) for s in self.category_keys()]
  self.mode_combo['values']=[self.tr(s) for s in ('Wireframe','Sólido','Texturizado')]
  self.kind_display.set(self.tr(self.kind.get()));self.mode_display.set(self.tr(self.render_mode.get()))
  for v in self.localized_vars:v.refresh()
  self.text.refresh()
  for i,key in enumerate(self.context_keys):self.context_tabs.tab(i,text=('Info' if self.language=='en' else 'Informações') if i==4 else self.tr(key))
  self.inspector_tabs.tab(0,text=self.tr('Informações'));self.inspector_tabs.tab(1,text=self.tr('Dependências'))
  self.build_menu()
 def set_language(self,language):
  if language not in ('pt-BR','en'):raise ValueError('Invalid UI language')
  self.language=language;self.language_display.set('English' if language=='en' else 'Português (Brasil)');self.refresh_language()
  self.language_settings.parent.mkdir(parents=True,exist_ok=True);self.language_settings.write_text(json.dumps({'language':language}),encoding='utf-8')
 def category_keys(self):return ['Todos','Modelos','Texturas','Áudio','Vídeo','Outros']+sorted({Path(a.name).suffix.lower() or '(sem extensão)' for a in self.assets})
 def select_display_category(self,event=None):
  self.kind.set(next((s for s in self.category_keys() if self.tr(s)==self.kind_display.get()),self.kind_display.get()));self.filter()
 def select_display_mode(self,event=None):
  value=self.mode_display.get();self.render_mode.set(next((s for s in ('Wireframe','Sólido','Texturizado') if self.tr(s)==value or s==value),value));self.draw()
 def dialog(self,name,**kwargs):
  if 'title' in kwargs:kwargs['title']=self.tr(kwargs['title'])
  if 'filetypes' in kwargs:kwargs['filetypes']=[(self.tr(label),pattern) for label,pattern in kwargs['filetypes']]
  return getattr(filedialog,name)(**kwargs)
 def message(self,name,title,message,**kwargs):return getattr(messagebox,name)(self.tr(title),self.tr(message),**kwargs)
 def worker(self,fn,done,label='Processando… Cancelar tarefa disponível.'):
  if self.busy:return
  import gc
  gc.collect()  # Dispose destroyed Tk dialog cycles on Tk thread, never a worker.
  self.busy=True;self.cancel_event.clear();self.progress.configure(mode='indeterminate');self.progress.start();self.status.set(label)
  for b in self.buttons:b.state(['disabled'])
  def run():
   try:self.events.put(('done',done,fn()))
   except Exception as e:self.events.put(('error',str(e)))
  self.thread=threading.Thread(target=run,daemon=True);self.thread.start()
 def cancel(self):self.cancel_event.set();self.player.stop();self.stop_video();self.status.set('Cancelamento solicitado; aguardando ponto seguro…')
 def poll(self):
  if self.closed:return
  try:
   while True:
    event=self.events.get_nowait()
    if event[0]=='progress':self.progress.stop();self.progress.configure(mode='determinate',maximum=event[2],value=event[1]);self.status.set(event[3] if len(event)>3 else f'Extraindo {event[1]}/{event[2]}');continue
    self.busy=False;self.progress.stop();self.progress.configure(mode='determinate',value=0)
    for b in self.buttons:b.state(['!disabled'])
    if event[0]=='done':
     try:event[1](event[2])
     except Exception as e:self.preview_error('Falha ao atualizar interface: '+str(e))
    else:
     self.preview_error(event[1])
     if 'Cancelado' not in event[1]:self.message('showerror','ORC Asset Explorer',event[1],parent=self.root)
  except queue.Empty:pass
  if not self.busy:
   if self.pending_selection:self.pending_selection=False;self.redraw_requested=False;self.select()
   elif self.redraw_requested:self.redraw_requested=False;self.draw()
  self.refresh_actions()
  self.poll_id=self.root.after(30,self.poll)
 def preview_error(self,message):
  self.status.set('Erro: '+message);self.text.delete('1.0','end');self.text.insert('1.0',message)
  import logging
  from logging.handlers import RotatingFileHandler
  logger=logging.getLogger('orc_explorer')
  if not logger.handlers:
   handler=RotatingFileHandler(media.home()/'explorer_errors.log',maxBytes=1024*1024,backupCount=1,encoding='utf-8');handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'));logger.addHandler(handler);logger.setLevel(logging.ERROR)
  logger.error('%s | source=%s | asset=%s',message,self.source_info.get(),self.info.get())
 def open_ssg(self):
  p=self.dialog('askopenfilename',title='Abrir SSG / Wwise',filetypes=[('SSG / backup / Wwise','*.ssg *.bak *.bnk *.pck'),('Todos','*.*')])
  if p:self.load(p)
 def open_folder(self):
  p=self.dialog('askdirectory',title='Abrir pasta extraída')
  if p:self.load(p)
 def load(self,p):
  if self.busy:return
  self.player.stop();self.stop_video();self.welcome.place_forget();self.preview_asset=None;self.pending_selection=False;self.redraw_requested=False
  def done(assets):
   self.gpu.place_forget();self.gpu_snapshot_key=None
   self.assets=assets;self.categories=[core.asset_category(a) for a in assets];self.context_tabs.availability(self.categories);self.mesh=None;self.detail=None;self.image=None;self.frames=[];self.bones=None;self.text.delete('1.0','end');self.canvas.delete('all');self.combo['values']=[self.tr(s) for s in self.category_keys()]
   model_count=self.categories.count('Modelos');texture_count=self.categories.count('Texturas')
   self.source_info.set(f'{Path(p).resolve()} • {len(assets)} assets • {model_count} modelos FM6S / {texture_count} texturas (inclui referências)')
   self.kind.set('Modelos' if model_count else 'Todos');self.search.set('');self.filter();self.status.set(f'Aberto: {model_count} modelos / {texture_count} texturas. Selecione um asset na lista para visualizar.');self.info.set(str(p))
   first=next((str(i) for i,a in enumerate(assets) if self.categories[i]=='Modelos' and a.read_head(8)[4:8] in (b'\x11\0\0\0',b'\x12\0\0\0')),None)
   if first is not None:self.tree.selection_set(first);self.tree.focus(first);self.tree.see(first)
   elif not model_count:self.info.set('Nenhuma malha FM6S neste arquivo. Use Todos os assets; IM6S é metadado, não geometria.')
  self.worker(lambda:core.open_source(p,self.cancel_event),done,label='Abrindo / indexando: '+str(p))
 def set_category(self,category):
  self.kind.set(category);self.search.set('');self.filter()
 def filter(self):
  self.preview_asset=None
  self.tree.delete(*self.tree.get_children());query=self.search.get().casefold();ext=self.kind.get()
  for i,a in enumerate(self.assets):
   category=self.categories[i] if len(self.categories)==len(self.assets) else core.asset_category(a)
   if query in a.name.casefold() and (ext=='Todos' or ext==category or (Path(a.name).suffix.lower() or '(sem extensão)')==ext):self.tree.insert('','end',iid=str(i),text=Path(a.name.replace('\\','/')).name,values=(a.size,))
  self.browser_count.set(f'{len(self.tree.get_children())} / {len(self.assets)} assets')
  self.clear_preview()
 def refresh_actions(self):
  a=self.selected();category=core.asset_category(a) if a else None
  requirements={'Exportar PNG…':self.image is not None,'Exportar quadro PNG…':self.image is not None and bool(self.frames),
   'Ajustar':self.image is not None,'Pixels 1:1':self.image is not None,'Usar imagem no modelo':self.image is not None,
   'Reproduzir':category=='Áudio' or bool(self.frames),'Parar':category=='Áudio','Pausar':bool(self.frames),
   'Exportar WAV…':category=='Áudio','Abrir banco selecionado':bool(a and Path(a.name).suffix.lower() in ('.bnk','.pck')),
   'Decodificar 10 segundos':category=='Vídeo','Texto / hex selecionado':a is not None,
   'Carregar esqueleto…':self.mesh is not None,'Referências de material':self.detail is not None,
   'Aplicar imagem guardada':self.detail is not None and hasattr(self,'manual_texture'),'Resetar câmera':self.mesh is not None or self.image is not None,
   'Extrair…':bool(self.assets)}
  for b in self.modern_buttons:
   label=self.label_sources[b]
   if label in requirements:b.configure(state='normal' if requirements[label] and not self.busy else 'disabled')
 def clear_preview(self):
  self.player.stop();self.stop_video();self.pending_selection=False;self.redraw_requested=False
  self.preview_asset=None;self.mesh=None;self.detail=None;self.image=None;self.photo=None;self.frames=[]
  self.gpu.place_forget();self.gpu_snapshot_key=None;self.canvas.delete('all');self.text.delete('1.0','end')
  self.info.set('Nenhum asset selecionado.');self.inspector_name.set('—');self.inspector_summary.set('Selecione um asset para inspecionar.')
  self.asset_caption.set('');self.status.set('Nenhum resultado.' if not self.tree.get_children() else 'Selecione para visualizar')
  self.canvas.create_text(20,30,anchor='nw',fill='white',text=self.status.get());self.refresh_actions()
 def selected(self):
  sel=self.tree.selection();return self.assets[int(sel[0])] if sel else None
 def select(self):
  a=self.selected()
  if not a or a is self.preview_asset:return
  if self.busy:self.pending_selection=True;return
  self.preview_asset=a;self.redraw_requested=False;self.mesh=None;self.detail=None
  self.player.stop();self.stop_video();self.info.set(f'{a.name} • {a.size:,} bytes')
  def get():
   try:
    if Path(a.name).suffix.lower()=='.edgemodel':
     if a.read_head(4)==b'IM6S':raise ValueError('IM6S é metadado de instância, não uma malha FM6S. Abra a malha referenciada.')
     return 'details',models.resolve(models.details(a.read()),self.assets)
    return core.preview(a)
   except Exception as e:return 'unavailable','Prévia indisponível: '+str(e)+'\n'+self.hex_asset(a)
  def done(result):
   if self.selected() is not a:return
   kind,value=result;self.context_sync=True
   self.active_context={'details':0,'image':1}.get(kind,{'Áudio':2,'Vídeo':3}.get(core.asset_category(a),4));self.context_tabs.select(self.active_context)
   self.present_context(self.active_context);self.root.update_idletasks();self.context_sync=False
   self.mesh=None;self.detail=None;self.image=None;self.photo=None;self.frames=[];self.text.delete('1.0','end');self.canvas.delete('all');self.gpu.place_forget();self.reset(draw=False)
   if kind=='details':self.render_mode.set('Texturizado' if value['textures'] else 'Sólido');self.detail=value;self.mesh=(value['vertices'],value['faces']);self.status.set(f"{len(value['vertices']):,} vértices • {len(value['faces']):,} triângulos • {len(value['textures'])} materiais com textura resolvida")
   elif kind=='image':self.image=value;self.status.set(f'Textura {value.width} × {value.height} • zoom/pan')
   elif kind=='unavailable':self.text.insert('1.0',value);self.status.set(a.name+' • '+value.split('\n')[0]);self.canvas.create_text(20,30,anchor='nw',width=max(100,self.canvas.winfo_width()-40),fill='white',text=value.split('\n')[0])
   else:self.text.insert('1.0',value);self.status.set('Metadados / texto / hex. Use seção Áudio ou Vídeo para decodificar.')
   self.draw()
  self.worker(get,done,label='Lendo prévia: '+a.name)
 def request_draw(self):
  if self.closed or self.render_id is not None:return
  def render_pending():self.render_id=None;self.draw()
  self.render_id=self.root.after_idle(render_pending)
 def draw(self):
  if self.closed:return
  w=max(self.canvas.winfo_width(),100);h=max(self.canvas.winfo_height(),100)
  if self.mesh is not None:
   d=self.detail or {'vertices':self.mesh[0],'faces':self.mesh[1],'textures':{}}
   if self.busy:self.redraw_requested=True;return
   if self.gpu.ready:
    try:
     if not self.gpu.winfo_ismapped():self.gpu.place(x=0,y=0,relwidth=1,relheight=1);self.gpu.update_idletasks()
     self.gpu.render_scene(d,self.yaw,self.pitch,self.zoom,self.render_mode.get(),self.bones if self.show_bones.get() else None,self.show_helpers.get(),pan=self.camera_pan)
     key=(id(d),self.render_mode.get(),w,h,self.show_helpers.get())
     if key!=self.gpu_snapshot_key:
      self.display(self.gpu.snapshot());self.canvas.create_text(10,10,anchor='nw',text='OpenGL');self.gpu_snapshot_key=key
     self.status.set(f"OpenGL • {len(d['vertices']):,} vértices / {len(d['faces']):,} triângulos • {len(d['textures'])} materiais com textura • {self.render_mode.get()} • {self.gpu.last_frame_ms:.2f} ms GPU concluída + swap / {1000/max(.001,self.gpu.last_frame_ms):.0f} FPS render (não scanout)")
     if d.get('warnings'):self.status.set(self.status.raw+f" • {len(d['warnings'])} avisos (alpha / shadow) — consulte referências de material")
    except Exception as e:self.preview_error('Render OpenGL: '+str(e))
    return
   self.gpu.place_forget();self.preview_error('GPU obrigatória: '+(self.gpu.error or 'Contexto OpenGL de hardware indisponível. Atualize o driver / selecione GPU de alto desempenho no Windows. Não há fallback CPU.'))
   self.canvas.create_text(20,30,anchor='nw',width=w-40,fill='white',text=self.status.get())
  elif self.image is not None:
   if not self.gpu.ready:self.gpu.place_forget();self.preview_error('GPU obrigatória: '+self.gpu.error);return
   try:
    if not self.gpu.winfo_ismapped():self.gpu.place(x=0,y=0,relwidth=1,relheight=1);self.gpu.update_idletasks()
    self.gpu.render_image(self.image,self.texture_zoom,self.pan)
    key=(id(self.image),w,h)
    if key!=self.gpu_snapshot_key:self.display(self.gpu.snapshot());self.gpu_snapshot_key=key
   except Exception as e:self.preview_error('Render imagem OpenGL: '+str(e))
 def display(self,image):self.photo=ImageTk.PhotoImage(image);self.canvas.delete('all');self.canvas.create_image(0,0,anchor='nw',image=self.photo)
 def orbit(self,e):
  x,y=self.drag;self.drag=(e.x,e.y)
  if self.mesh is not None:self.yaw+=(e.x-x)*.01;self.pitch+=(e.y-y)*.01
  elif self.image is not None:self.pan=(self.pan[0]+e.x-x,self.pan[1]+e.y-y)
  self.request_draw()
 def pan_camera(self,e):
  x,y=self.drag;self.drag=(e.x,e.y)
  if self.mesh is not None:
   self.camera_pan=(self.camera_pan[0]+e.x-x,self.camera_pan[1]+e.y-y)
   self.request_draw()
  elif self.image is not None:
   self.pan=(self.pan[0]+e.x-x,self.pan[1]+e.y-y);self.request_draw()
 def wheel(self,e):
  factor=1.1 if e.delta>0 else 1/1.1
  if self.mesh is not None:self.zoom=max(.1,min(20,self.zoom*factor))
  elif self.image is not None:self.texture_zoom=max(.05,min(64,self.texture_zoom*factor))
  self.request_draw()
 def reset(self,e=None,draw=True):
  self.yaw=.4;self.pitch=.1;self.zoom=1;self.texture_zoom=1;self.pan=(0,0);self.camera_pan=(0,0)
  if draw:self.draw()
 def actual_texture(self):
  if self.image is not None:self.texture_zoom=1/min(max(100,self.canvas.winfo_width())/self.image.width,max(100,self.canvas.winfo_height())/self.image.height);self.pan=(0,0);self.draw()
 def apply_texture(self):
  if self.image is None:return
  self.manual_texture=self.image.copy();self.status.set('Imagem guardada: selecione modelo para aplicar manualmente aos UVs. Não é resolução automática de material.')
 def show_materials(self):
  if self.detail is not None:
   self.present_context(4)
   self.text.delete('1.0','end');self.text.insert('1.0','\n'.join(self.detail['materials']+self.detail['references']+self.detail.get('warnings',[])))
 def apply_manual(self):
  if self.detail is not None and hasattr(self,'manual_texture'):
   self.detail['textures']={i:self.manual_texture.convert('RGBA') for i in range(len(self.detail['materials']))};self.gpu.loaded=None;self.gpu_snapshot_key=None;self.render_mode.set('Texturizado');self.draw();self.status.set('Textura manual aplicada a todos os materiais; não representa materiais originais.')
 def load_skeleton(self):
  p=self.dialog('askopenfilename',title='Edge skeleton (não HKX)')
  if p:self.worker(lambda:models.skeleton(Path(p).read_bytes()),self.set_skeleton)
 def set_skeleton(self,bones):self.bones=bones;self.status.set(f'{len(bones[0])} juntas • skeleton escolhido manualmente • sem skinning/animação');self.draw()
 def extract(self,all_assets):
  assets=self.assets if all_assets else [self.assets[int(i)] for i in self.tree.selection()]
  if not assets:self.message('showinfo','Extração','Selecione pelo menos um asset.');return
  p=self.dialog('askdirectory',title='Pasta fora da origem/jogo; nunca sobrescreve')
  if p:self.worker(lambda:core.extract(assets,p,lambda n,total:self.events.put(('progress',n,total)),self.cancel_event),lambda paths:self.status.set(f'Extração concluída: {len(paths)} arquivos em {p}'))
 def play(self):
  a=self.selected()
  if a:self.worker(lambda:self.player.play(a,self.cancel_event),lambda text:self.status.set(text))
 def open_bank(self):
  a=self.selected()
  if not a:return
  if getattr(a,'path',None) and a.path.suffix.lower() in ('.bnk','.pck'):self.load(a.path)
  else:self.message('showinfo','Banco','Abra o BNK/PCK em Arquivo / Extração. Bancos embutidos devem ser extraídos primeiro.')
 def export_wav(self):
  a=self.selected()
  if not a:return
  p=self.dialog('asksaveasfilename',title='Exportar WAV (não sobrescreve)',defaultextension='.wav')
  if not p:return
  def get():
   decoded=self.player.decode(a,self.cancel_event);dest=Path(p)
   core.extract([core.Asset(dest.name,decoded.read_bytes(),source=a.source)],dest.parent,cancel=self.cancel_event)
   return str(dest)
  self.worker(get,lambda path:self.status.set('WAV exportado: '+path))
 def decode_video(self):
  a=self.selected()
  if not a:return
  try:start=float(self.video_start.get())
  except ValueError:self.message('showerror','Vídeo','Início deve ser número de segundos.');return
  def get():
   if getattr(a,'path',None) and not hasattr(a,'offset'):return media.video_frames(a.path,start=start,cancel=self.cancel_event)
   with tempfile.TemporaryDirectory(dir=media.home()/'cache') as temp:
    p=Path(temp)/('input'+Path(a.name).suffix);p.write_bytes(a.read());return media.video_frames(p,start=start,cancel=self.cancel_event)
  self.worker(get,self.set_video)
 def set_video(self,frames):self.frames=frames;self.mesh=None;self.detail=None;self.image=frames[0];self.video_index=0;self.reset();self.status.set(f'{len(frames)} quadros reais FFmpeg • 12 fps • até 10s • sem áudio sincronizado');self.start_video()
 def start_video(self):
  self.stop_video()
  if not self.frames:return
  def tick():
   if self.closed:return
   self.image=self.frames[self.video_index%len(self.frames)];self.video_index+=1;self.draw()
   if self.video_index<len(self.frames):self.video_id=self.root.after(83,tick)
   else:self.video_id=None
  self.video_index=0;tick()
 def stop_video(self):
  if self.video_id is not None:self.root.after_cancel(self.video_id);self.video_id=None
 def export_png(self):
  if self.image is None:return
  p=self.dialog('asksaveasfilename',title='Exportar PNG (não sobrescreve)',defaultextension='.png')
  if p:
   try:
    import io
    buffer=io.BytesIO();self.image.save(buffer,format='PNG');dest=Path(p);a=self.selected();core.extract([core.Asset(dest.name,buffer.getvalue(),source=a.source if a else None)],dest.parent)
    self.status.set('PNG exportado: '+p)
   except Exception as e:self.message('showerror','Exportar PNG',str(e))
 def hex_asset(self,a):
  if hasattr(a,'chunks'):data=next(a.chunks(),b'')[:4096]
  elif a.data is not None:data=a.data[:4096]
  else:
   with a.path.open('rb') as f:data=f.read(4096)
  return a.name+'\n'+ '\n'.join(f'{i:08X}  '+data[i:i+16].hex(' ') for i in range(0,min(1024,len(data)),16))
 def show_hex(self):
  self.present_context(4)
  a=self.selected()
  if a:self.text.delete('1.0','end');self.text.insert('1.0',self.hex_asset(a))
 def help(self):self.present_context(4);self.text.delete('1.0','end');self.text.insert('1.0','FM6S 17/18; GPU OpenGL obrigatória, sem fallback CPU ou shaders originais do jogo. A linha GPU identifica hardware/contexto real. Abra SSG completo: Modelos/primeira malha são selecionados automaticamente. IM6S não é geometria. Skeleton em bind pose, sem skinning/animação. Texturas externas/referências de 4 bytes requerem arquivos completos. Wwise lista mídia, não simula eventos. Vídeo: prévia até 10s/12fps sem áudio sincronizado. SSG <=1GB, cache <=4GB. Cancelamento preserva concluídos e remove parcial. FPS no benchmark inclui GPU concluída + swap, não scanout físico. Upload inicial pode pausar brevemente. Leia README pt-BR/English. Não redistribua assets do jogo.')
 def choose_dep(self,key):
  p=self.dialog('askopenfilename',title='Selecionar executável oficial '+key,filetypes=[('Executável','*.exe')])
  if p:self.dep_vars[key].set(p)
 def save_deps(self):
  values={k:v.get().strip() for k,v in self.dep_vars.items()}
  for key,p in values.items():self.dependency_status[key].set('Detecção: '+('Detectado' if p and Path(p).is_file() else 'Não detectado'))
  invalid=[key for key,p in values.items() if p and not Path(p).is_file()]
  if invalid:
   self.settings_feedback.set('Caminho não encontrado. '+', '.join(invalid));self.settings_feedback_label.configure(foreground='#f1a6a6');return False
  try:
   target=media.home()/'dependencies.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(values,indent=2),encoding='utf-8')
  except OSError as error:
   self.settings_feedback.set('Não foi possível salvar caminhos: '+str(error));self.settings_feedback_label.configure(foreground='#f1a6a6');return False
  self.player.refresh();self.status.set('Caminhos salvos. Use somente executáveis oficiais confiáveis.');self.settings_feedback.set('Caminhos salvos.');self.settings_feedback_label.configure(foreground='#a4d7b5');return True
 def close(self):
  if self.closed:return
  if self.busy:
   self.cancel();self.status.set('Fechando: aguardando cancelamento seguro…');self.close_id=self.root.after(100,self.close);return
  self.closed=True;self.root.after_cancel(self.poll_id)
  for tip in self.tooltips:tip.hide()
  if self.render_id is not None:self.root.after_cancel(self.render_id);self.render_id=None
  self.stop_video();self.progress.stop();self.player.close();self.assets=[]
  # CTk appearance/DPI timers are interpreter-scoped. Cancel every callback
  # owned by this application interpreter before destroying widget commands.
  for timer in self.root.tk.call('after','info'):self.root.after_cancel(timer)
  self.root.destroy()
def main():
 if len(sys.argv)>2 and sys.argv[1] in ('--smoke-test','--smoke-test-v2','--smoke-editor','--smoke-settings','--smoke-qa-fixes','--user-journey','--benchmark-gpu','--smoke-camera','--smoke-full-export'):
  import traceback
  try:
   if sys.argv[1] in ('--user-journey','--benchmark-gpu'):
    import smoke_journey;smoke_journey.run(sys.argv[2],benchmark=True)
   elif sys.argv[1]=='--smoke-full-export':
    import full_export_qa_runner;full_export_qa_runner.run(sys.argv[2])
   elif sys.argv[1]=='--smoke-camera':
    import camera_qa_runner;camera_qa_runner.run(sys.argv[2])
   elif sys.argv[1]=='--smoke-settings':
    import settings_qa_runner;settings_qa_runner.run(sys.argv[2])
   elif sys.argv[1]=='--smoke-qa-fixes':
    import qa_fixes_runner;qa_fixes_runner.run(sys.argv[2])
   elif sys.argv[1]=='--smoke-editor':
    import smoke_editor;smoke_editor.run(sys.argv[2])
   elif sys.argv[1]=='--smoke-test-v2':
    import smoke_v2;smoke_v2.run(sys.argv[2])
   else:
    import smoke;smoke.run(sys.argv[2])
  except Exception:
   Path(sys.argv[2]).mkdir(parents=True,exist_ok=True);(Path(sys.argv[2])/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
   # Owned QA reports retain the full traceback; avoid PyInstaller's unhandled
   # exception popup on the user's desktop while still returning failure.
   raise SystemExit(1)
  return
 root=tk.Tk();app=Explorer(root)
 if len(sys.argv)>1 and not sys.argv[1].startswith('--'):app.load(sys.argv[1])
 root.mainloop()
if __name__=='__main__':main()

