"""Original contemporary native desktop shell. Tk/WGL engine, CTk controls.
No web UI, gradients, copied CSS, or CPU model rendering.
"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import i18n, media
from pathlib import Path

BG='#202124';SURFACE='#292b2f';INK='#f2f3f5';MUTED='#adb0b7';ACCENT='#83bcf1'

class Button(ctk.CTkButton):
 def __init__(self,parent,text,command,primary=False,width=100,**kw):
  self.style_name='Accent.TButton' if primary else 'TButton'
  super().__init__(parent,text=text,command=command,width=width,height=32,corner_radius=8,border_width=0,
   fg_color=ACCENT if primary else 'transparent',hover_color='#a1cdf6' if primary else '#36393e',
   text_color='#15212c' if primary else INK,font=('Segoe UI',13),**kw)
  self._canvas.configure(takefocus=True)
  self.bind('<Return>',lambda e:self.invoke());self.bind('<space>',lambda e:self.invoke())
  self.bind('<FocusIn>',lambda e:self.configure(border_width=1,border_color=ACCENT))
  self.bind('<FocusOut>',lambda e:self.configure(border_width=0))
 def state(self,values=None):
  if values is None:return ('disabled',) if self.cget('state')=='disabled' else ()
  self.configure(state='disabled' if 'disabled' in values else 'normal')
 def cget(self,key):
  if key=='style':return self.style_name
  return super().cget(key)
 def configure(self,**kw):
  if 'style' in kw:self.style_name=kw.pop('style')
  return super().configure(**kw)

class Navigation(ttk.Frame):
 """Native rounded segmented navigation; compatible event API, no Notebook chrome."""
 def __init__(self,parent,**kw):
  kw.pop('height',None);super().__init__(parent,**kw);self.buttons=[];self.pages=[];self.current=0
 def add(self,page,text):
  index=len(self.buttons);self.pages.append(page)
  b=Button(self,text,lambda:self.select(index),width=76 if index!=4 else 100)
  b.pack(side='left',padx=(0,4));self.buttons.append(b);self.paint()
 def tabs(self):return tuple(str(p) for p in self.pages)
 def index(self,index):return self.current if index=='current' else int(index)
 def select(self,index=None):
  if index is None:return str(self.pages[self.current])
  index=int(index);changed=index!=self.current;self.current=index;self.paint()
  if changed:self.event_generate('<<NotebookTabChanged>>',when='tail')
 def tab(self,index,option=None,**kw):
  b=self.buttons[int(index)]
  if 'text' in kw:b.configure(text=kw['text'])
  if option=='text':return b.cget('text')
  return {'text':b.cget('text')}
 def availability(self,categories):
  for i,key in enumerate(['Modelos','Texturas','Áudio','Vídeo','Outros']):
   self.buttons[i].configure(state='normal' if i==4 or key in categories else 'disabled')
 def paint(self):
  for i,b in enumerate(self.buttons):b.configure(fg_color='#354a5d' if i==self.current else 'transparent',text_color=ACCENT if i==self.current else MUTED)

class Section(ttk.Frame):
 def __init__(self,parent,title,opened=True,collapsible=False):
  super().__init__(parent);self.title=title;self.opened=opened;self.collapsible=collapsible
  self.header=Button(self,title,self.toggle,width=160) if collapsible else ttk.Label(self,text=title,style='Section.TLabel')
  self.header.pack(fill='x',pady=(16,8));self.body=ttk.Frame(self);self.refresh()
 def refresh(self):
  owner=self.winfo_toplevel();translate=getattr(owner,'_translate',lambda s:s)
  self.header.configure(text=('›  ' if not self.opened else '⌄  ')+translate(self.title) if self.collapsible else translate(self.title))
  if self.opened:self.body.pack(fill='x')
  else:self.body.pack_forget()
 def toggle(self):self.opened=not self.opened;self.refresh()

def build(a):
 root=a.root
 ctk.set_appearance_mode('dark');ctk.set_widget_scaling(1);ctk.set_window_scaling(1)
 a.modern_buttons=[];a.file_actions={};a.tooltips=[]
 def button(parent,label,cmd,primary=False,width=100,managed=True):
  b=Button(parent,label,cmd,primary,width);a.modern_buttons.append(b);a.label_sources[b]=label
  if managed:a.buttons.append(b)
  return b
 def row(parent):
  f=ttk.Frame(parent);f.pack(fill='x',pady=4);return f
 def small(parent,label,cmd,width=100,managed=True):
  b=button(parent,label,cmd,width=width,managed=managed);b.pack(side='left',padx=(0,4));return b
 def label(parent,text,**kw):
  w=ttk.Label(parent,text=text,**kw);w.pack(anchor='w');return w
 # One command strip. Overflow menus preserve capabilities without duplication.
 tools=ttk.Frame(root,padding=(16,12));tools.pack(fill='x');a.toolbar=tools
 brand=ttk.Label(tools,text='ORC',style='Brand.TLabel');brand.pack(side='left',padx=(0,16))
 label_title=ttk.Label(tools,text='Asset Explorer',style='Heading.TLabel');label_title.pack(side='left',padx=(0,24))
 open_button=button(tools,'Abrir…',lambda:popup(a.open_menu,open_button),True,96);open_button.pack(side='left',padx=(0,8));a.file_actions['open']=open_button
 extract_button=button(tools,'Extrair…',lambda:popup(a.extract_menu,extract_button),width=96);extract_button.pack(side='left');a.file_actions['extract']=extract_button
 settings=button(tools,'Configurações',a.show_settings,width=114,managed=False);settings.pack(side='right')
 a.language_display=tk.StringVar(value='English' if a.language=='en' else 'Português (Brasil)')
 language_selector=ttk.Combobox(tools,textvariable=a.language_display,values=['Português (Brasil)','English'],state='readonly',width=17);language_selector.pack(side='right',padx=(8,16));language_selector.bind('<<ComboboxSelected>>',lambda e:a.set_language('en' if a.language_display.get()=='English' else 'pt-BR'))
 a.language_selector=language_selector
 tk.Frame(root,bg='#34363b',height=1).pack(fill='x')
 a.editor_pane=ttk.Panedwindow(root,orient='horizontal');a.editor_pane.pack(fill='both',expand=True,padx=8,pady=8)
 a.browser=ttk.Frame(a.editor_pane,width=248,padding=(12,8));a.viewport=ttk.Frame(a.editor_pane,padding=(8,0));a.inspector=ttk.Frame(a.editor_pane,width=272,padding=(16,8))
 for f,w in [(a.browser,0),(a.viewport,1),(a.inspector,0)]:a.editor_pane.add(f,weight=w)
 label(a.browser,'Biblioteca',style='Heading.TLabel')
 a.source_info=a.localized_var(value='Fontes somente leitura • extração sem sobrescrever')
 a.source_caption=tk.StringVar(value='SSG · BNK · PCK · pasta')
 ttk.Label(a.browser,textvariable=a.source_caption,style='Muted.TLabel',wraplength=212).pack(fill='x',pady=(8,16))
 a.source_info.trace_add('write',lambda *args:update_source(a))
 label(a.browser,'Pesquisar assets',style='Muted.TLabel')
 a.search=tk.StringVar()
 a.search_entry=ctk.CTkEntry(a.browser,textvariable=a.search,height=36,corner_radius=8,border_width=0,fg_color=SURFACE,text_color=INK,placeholder_text='Pesquisar assets',font=('Segoe UI',13))
 a.search_entry.pack(fill='x',pady=(0,8));a.search_entry.bind('<FocusIn>',lambda e:a.search_entry.configure(border_width=1,border_color=ACCENT),add='+');a.search_entry.bind('<FocusOut>',lambda e:a.search_entry.configure(border_width=0),add='+')
 a.kind=tk.StringVar(value='Todos');a.kind_display=tk.StringVar(value=a.tr('Todos'))
 a.combo=ttk.Combobox(a.browser,textvariable=a.kind_display,values=[a.tr('Todos')],state='readonly');a.combo.pack(fill='x',pady=(0,8))
 a.search.trace_add('write',lambda *args:a.filter());a.combo.bind('<<ComboboxSelected>>',a.select_display_category);a.kind.trace_add('write',lambda *args:a.kind_display.set(a.tr(a.kind.get())))
 a.browser_count=a.localized_var(value='0 / 0 assets');ttk.Label(a.browser,textvariable=a.browser_count,style='Muted.TLabel').pack(fill='x',pady=(8,8))
 left=ttk.Frame(a.browser);left.pack(fill='both',expand=True)
 a.tree=ttk.Treeview(left,columns=('size',),show='tree',selectmode='extended');a.tree.heading('#0',text='Asset');a.tree.heading('size',text='Bytes');a.tree.column('#0',width=190,minwidth=120);a.tree.column('size',width=0,minwidth=0,stretch=False)
 a.tree.pack(side='left',fill='both',expand=True);scroll=ctk.CTkScrollbar(left,command=a.tree.yview,width=10,fg_color=BG,button_color='#45484e',button_hover_color='#5a5e65');scroll.pack(side='right',fill='y');a.tree.configure(yscrollcommand=scroll.set);a.tree.bind('<<TreeviewSelect>>',lambda e:a.select())
 # Flat library: a double click must select, not toggle a nonexistent tree
 # branch. Tk's class double-click binding skips selection after refiltering.
 def double_select(event):
  iid=a.tree.identify_row(event.y)
  if iid:a.tree.selection_set(iid);a.tree.focus(iid)
  return 'break'
 a.tree.bind('<Double-Button-1>',double_select)
 a.library_status=a.localized_var(value='Selecione para visualizar')
 ttk.Label(a.browser,textvariable=a.library_status,style='Muted.TLabel',wraplength=212).pack(fill='x')
 # Real context tabs and an economical inline viewport toolbar.
 a.context_tabs=Navigation(a.viewport);a.context_tabs.pack(fill='x',pady=(0,8));a.context_keys=['Modelo','Textura','Áudio','Vídeo','Informações']
 for key in a.context_keys:a.context_tabs.add(ttk.Frame(a.context_tabs),text=key)
 a.context_tabs.availability([])
 a.context_tabs.bind('<<NotebookTabChanged>>',a.context_changed)
 a.info=a.localized_var(value='Abra um SSG, banco Wwise ou pasta para começar.')
 a.asset_caption=tk.StringVar(value='');a.asset_caption_label=ttk.Label(a.viewport,textvariable=a.asset_caption,style='Heading.TLabel');a.asset_caption_label.pack(fill='x',pady=(8,4))
 a.info.trace_add('write',lambda *args:update_asset(a))
 a.viewport_tools=row(a.viewport)
 a.render_mode=tk.StringVar(value='Sólido');a.mode_display=tk.StringVar(value=a.tr('Sólido'))
 a.mode_combo=ttk.Combobox(a.viewport_tools,textvariable=a.mode_display,values=[a.tr(s) for s in ('Wireframe','Sólido','Texturizado')],state='readonly',width=13);a.mode_combo.pack(side='left');a.mode_combo.bind('<<ComboboxSelected>>',a.select_display_mode);a.render_mode.trace_add('write',lambda *args:a.mode_display.set(a.tr(a.render_mode.get())))
 small(a.viewport_tools,'Resetar câmera',a.reset,116,False)
 b=button(a.context_tabs,'Inspetor',a.toggle_inspector,width=76,managed=False);b.pack(side='right')
 a.canvas=tk.Canvas(a.viewport,bg='#202124',highlightthickness=0);a.canvas.pack(fill='both',expand=True,pady=(8,0));a.canvas.bind('<ButtonPress-1>',lambda e:setattr(a,'drag',(e.x,e.y)));a.canvas.bind('<B1-Motion>',a.orbit);a.canvas.bind('<MouseWheel>',a.wheel);a.canvas.bind('<Double-Button-1>',a.reset);a.canvas.bind('<Configure>',lambda e:a.request_draw())
 from gpu_preview import GPUPreview
 a.gpu_info=a.localized_var(value='GPU obrigatória • iniciando contexto OpenGL de hardware…')
 a.gpu=GPUPreview(a.canvas,on_error=lambda t:a.gpu_info.set(t),on_context=lambda info:a.gpu_info.set('GPU: '+info['GL_RENDERER']+' • '+info['GL_VENDOR']+' • OpenGL '+info['GL_VERSION']));a.gpu_snapshot_key=None
 a.gpu.place(x=0,y=0,relwidth=1,relheight=1)
 a.gpu.bind('<ButtonPress-1>',lambda e:setattr(a,'drag',(e.x,e.y)));a.gpu.bind('<B1-Motion>',a.orbit);a.gpu.bind('<MouseWheel>',a.wheel);a.gpu.bind('<Double-Button-1>',a.reset);a.gpu.bind('<Configure>',lambda e:a.request_draw(),add='+')
 a.gpu.bind('<ButtonPress-3>',lambda e:setattr(a,'drag',(e.x,e.y)));a.gpu.bind('<B3-Motion>',a.pan_camera)
 a.gpu.bind('<ButtonPress-2>',lambda e:setattr(a,'drag',(e.x,e.y)));a.gpu.bind('<B2-Motion>',a.pan_camera)
 a.welcome=ttk.Frame(a.canvas,padding=24);a.welcome.place(relx=.5,rely=.5,anchor='center')
 label(a.welcome,'Explore os arquivos do jogo',style='Title.TLabel')
 ttk.Label(a.welcome,text='Abrir → Selecionar → Visualizar → Extrair',style='Muted.TLabel').pack(anchor='w',pady=(16,8))
 ttk.Label(a.welcome,text='Use Abrir no topo ou Ctrl+O.\nNenhum arquivo de origem será alterado.',style='Muted.TLabel').pack(anchor='w',pady=8)
 a.text=i18n.LocalizedText(a.viewport,a,height=5,wrap='word',relief='flat',padx=16,pady=16)
 a.text.pack_forget()
 hint=ttk.Label(a.viewport,text='Esquerdo: orbitar · Direito/meio: mover\nRoda: zoom · Duplo clique: reset',style='Muted.TLabel');hint.pack(fill='x',pady=(8,0));a.viewport_hint=hint
 # A property inspector, not a second toolbar.
 label(a.inspector,'Propriedades',style='Heading.TLabel')
 a.inspector_name=tk.StringVar(value='—');ttk.Label(a.inspector,textvariable=a.inspector_name,wraplength=228,style='Section.TLabel').pack(fill='x',pady=(24,8))
 a.inspector_summary=a.localized_var(value='Selecione um asset para inspecionar.');ttk.Label(a.inspector,textvariable=a.inspector_summary,wraplength=228,style='Muted.TLabel').pack(fill='x',pady=(0,8))
 a.inspector_content=ttk.Frame(a.inspector);a.inspector_content.pack(fill='both',expand=True)
 a.hidden_controls=ttk.Frame(a.inspector)
 for name in ['Arquivo / Extração','Modelos','Texturas','Áudio','Vídeo','Informações']:
  a.sections[name]=Section(a.hidden_controls if name=='Arquivo / Extração' else a.inspector_content,name)
 a.show_bones=tk.BooleanVar(value=True);a.show_helpers=tk.BooleanVar(value=False)
 model=a.sections['Modelos'].body
 ttk.Label(model,text='Materiais resolvidos automaticamente',wraplength=220,style='Muted.TLabel').pack(fill='x',pady=8)
 a.advanced_model=Section(model,'Avançado: materiais / rig',False,True);a.advanced_model.pack(fill='x')
 adv=a.advanced_model.body
 ttk.Checkbutton(adv,text='Overlay esqueleto',variable=a.show_bones,command=a.draw).pack(fill='x',pady=4)
 ttk.Checkbutton(adv,text='Helpers shadow',variable=a.show_helpers,command=a.draw).pack(fill='x',pady=4)
 for text,cmd in [('Exportar modelos (Blender)…',a.show_export_dialog),('Carregar esqueleto…',a.load_skeleton),('Referências de material',a.show_materials),('Aplicar imagem guardada',a.apply_manual)]:
  rr=row(adv);small(rr,text,cmd,214)
 texture=a.sections['Texturas'].body
 rr=row(texture);small(rr,'Ajustar',a.reset,92);small(rr,'Pixels 1:1',a.actual_texture,102)
 rr=row(texture);small(rr,'Exportar PNG…',a.export_png,132)
 manual=Section(texture,'Avançado: textura manual',False,True);manual.pack(fill='x');a.manual_section=manual
 rr=row(manual.body);small(rr,'Usar imagem no modelo',a.apply_texture,214)
 audio=a.sections['Áudio'].body
 rr=row(audio);small(rr,'Reproduzir',a.play,108);small(rr,'Parar',a.player.stop,80,False)
 rr=row(audio);small(rr,'Exportar WAV…',a.export_wav,132)
 rr=row(audio);small(rr,'Abrir banco selecionado',a.open_bank,214)
 ttk.Label(audio,text='Mídia Wwise requer vgmstream.\nEventos HIRC não são simulados.',style='Muted.TLabel',wraplength=220).pack(fill='x',pady=16)
 video=a.sections['Vídeo'].body
 rr=row(video);ttk.Label(rr,text='Início (s)').pack(side='left');a.video_start=tk.StringVar(value='0');ttk.Entry(rr,textvariable=a.video_start,width=10).pack(side='right')
 rr=row(video);small(rr,'Decodificar 10 segundos',a.decode_video,214)
 rr=row(video);small(rr,'Reproduzir',a.start_video,108,False);small(rr,'Pausar',a.stop_video,80,False)
 rr=row(video);small(rr,'Exportar quadro PNG…',a.export_png,214)
 ttk.Label(video,text='Até 10 s · 12 fps\nSem áudio sincronizado',style='Muted.TLabel').pack(fill='x',pady=16)
 info=a.sections['Informações'].body
 rr=row(info);small(rr,'Texto / hex selecionado',a.show_hex,214)
 # Separate modern native Settings; retain the same dependency actions.
 import settings_ui
 settings_ui.build(a)
 # Compact status with explicit expandable diagnostics. Detailed state is retained.
 a.status=a.localized_var(value='Pronto');a.status_caption=tk.StringVar(value=a.tr('Pronto'))
 a.status.trace_add('write',lambda *args:update_status(a))
 a.log_panel=ttk.Frame(root,padding=(16,8))
 ttk.Label(a.log_panel,textvariable=a.status,wraplength=1280,style='Muted.TLabel').pack(fill='x')
 ttk.Label(a.log_panel,textvariable=a.gpu_info,wraplength=1280,style='Muted.TLabel').pack(fill='x',pady=(4,0))
 ttk.Label(a.log_panel,textvariable=a.source_info,wraplength=1280,style='Muted.TLabel').pack(fill='x',pady=(4,0))
 a.statusbar=ttk.Frame(root,padding=(16,4));a.statusbar.pack(side='bottom',fill='x',before=a.editor_pane)
 a.cancel_button=button(a.statusbar,'Cancelar tarefa',a.cancel,width=128,managed=False);a.cancel_button.pack(side='right')
 b=button(a.statusbar,'Detalhes',a.toggle_log,width=82,managed=False);b.pack(side='right',padx=(8,0))
 ttk.Label(a.statusbar,textvariable=a.status_caption,style='Muted.TLabel').pack(side='left',fill='x',expand=True)
 a.progress=ttk.Progressbar(root);a.progress.pack(side='bottom',fill='x',before=a.statusbar);root.protocol('WM_DELETE_WINDOW',a.close);a.poll_id=root.after(30,a.poll)
 a.pending_selection=False;a.redraw_requested=False;a.preview_asset=None
 root.bind('<Control-f>',lambda e:a.search_entry.focus_set())
 root.bind('<Configure>',lambda e:responsive(a) if e.widget is root else None,add='+')
 a.layout_width=None

def popup(menu,widget):menu.tk_popup(widget.winfo_rootx(),widget.winfo_rooty()+widget.winfo_height()+4)

def update_source(a):
 raw=a.source_info.raw
 path=raw.split(' • ')[0]
 a.source_caption.set(Path(path).name if ('/' in path or '\\' in path) else 'SSG · BNK · PCK · '+a.tr('pasta'))

def update_asset(a):
 selected=a.selected()
 a.asset_caption.set(Path(selected.name.replace('\\','/')).name if selected else '')
 a.inspector_name.set(Path(selected.name.replace('\\','/')).name if selected else '—')
 if selected:a.inspector_summary.set(f'{selected.size:,} bytes\n'+selected.name)
 a.library_status.set('Selecionado: '+Path(selected.name.replace('\\','/')).name if selected else 'Selecione para visualizar')

def update_status(a):
 value=a.status.get();short=value.split('\n')[0]
 if short.startswith('OpenGL'):
  short='OpenGL · '+a.tr(a.render_mode.get())+' · '+a.tr('Fontes somente leitura')
 elif len(short)>94:short=short[:91]+'…'
 a.status_caption.set(short)
 if a.detail is not None:
  d=a.detail;a.inspector_summary.set(f"{len(d['vertices']):,} vértices\n{len(d['faces']):,} triângulos\n{len(d['textures'])} materiais com textura\n"+f"{len(d.get('warnings',[]))} "+a.tr('avisos (alpha / shadow)'))
 elif a.image is not None:a.inspector_summary.set(f'{a.image.width} × {a.image.height} px\nRGBA · '+a.tr('zoom/pan'))

def responsive(a):
 width=a.root.winfo_width()
 bucket=width<1180
 if getattr(a,'layout_width',None)!=bucket:
  a.layout_width=bucket
  a.root.after_idle(a.fit_editor_panes)

def inspector_context(a,index):
 for name in ['Modelos','Texturas','Áudio','Vídeo','Informações']:a.sections[name].pack_forget()
 key=['Modelos','Texturas','Áudio','Vídeo','Informações'][index]
 a.sections[key].pack(fill='x')
 if index==0:a.viewport_tools.pack(fill='x',after=a.asset_caption_label if hasattr(a,'asset_caption_label') else a.context_tabs,pady=4)
 else:a.viewport_tools.pack_forget()
 a.viewport_hint.configure(text=a.tr('Esquerdo: orbitar · Direito/meio: mover\nRoda: zoom · Duplo clique: reset') if index==0 else a.tr('Roda para zoom · arraste para mover') if index==1 else '')
