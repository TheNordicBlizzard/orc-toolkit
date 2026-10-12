"""Localized real batch and optional Blender export dialogs."""
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import json,os
import batch_extract,blender_export,core

def window(a,title):
 w=tk.Toplevel(a.root);w.title(a.tr(title));w.geometry('760x620');w.minsize(680,560);w.transient(a.root);w._translate=a.tr
 body=ttk.Frame(w,padding=20);body.pack(fill='both',expand=True)
 ttk.Label(body,text=a.tr(title),style='Title.TLabel').pack(anchor='w',pady=(0,12))
 w.feedback=tk.StringVar();ttk.Label(body,textvariable=w.feedback,wraplength=700).pack(side='bottom',fill='x',pady=12)
 def close():
  if a.busy:a.cancel();w.feedback.set(a.tr('Cancelamento solicitado; aguardando ponto seguro…'))
  else:w.destroy()
 w.protocol('WM_DELETE_WINDOW',close);return w,body

def path_row(a,w,body,label,folder=True):
 ttk.Label(body,text=a.tr(label)).pack(anchor='w',pady=(8,4));row=ttk.Frame(body);row.pack(fill='x');v=tk.StringVar()
 ttk.Entry(row,textvariable=v).pack(side='left',fill='x',expand=True)
 def browse():
  p=a.dialog('askdirectory' if folder else 'askopenfilename',parent=w,title=label)
  if p:v.set(p)
 ttk.Button(row,text=a.tr('Selecionar…'),command=browse).pack(side='right',padx=(8,0));return v

def batch_dialog(a):
 w,b=window(a,'Extrair jogo completo…');w.source_var=path_row(a,w,b,'Pasta de instalação (somente leitura)');w.destination_var=path_row(a,w,b,'Destino novo ou vazio fora do jogo')
 w.loose_var=tk.BooleanVar(value=True);w.banks_var=tk.BooleanVar(value=False);w.media_var=tk.BooleanVar(value=False)
 for text,v in [('Preservar assets loose relevantes',w.loose_var),('Incluir bancos BNK / PCK',w.banks_var),('Extrair mídia dos bancos (sem eventos / decodificação)',w.media_var)]:ttk.Checkbutton(b,text=a.tr(text),variable=v).pack(anchor='w',pady=4)
 ttk.Label(b,text=a.tr('Inventário sem extrair. EXE, DLL, DRM e arquivos de configuração/credenciais são excluídos. Sem seguir junctions. Espaço é estimado, não garantido; limite SSG 1 GB / cache 4 GB.'),wraplength=700).pack(fill='x',pady=12)
 w.inventory=None
 def invalid(error):w.feedback.set(str(error))
 def inventoried(inv):
  if not w.winfo_exists():return
  w.inventory=inv;w.feedback.set(a.tr('Inventário: ')+f"{len(inv['items'])} assets | SSG: {sum(i['kind']=='ssg' for i in inv['items'])} | {inv['estimated_output_bytes']:,} bytes + cache | unknown: {inv['estimate_unknown']} | reparse skipped: {len(inv['reparse_skipped'])}")
 def scan():
  if a.busy:return
  source=w.source_var.get();loose=w.loose_var.get();banks=w.banks_var.get()
  if not source:return invalid(a.tr('Selecione instalação e destino.'))
  a.worker(lambda:batch_extract.inventory(source,loose,banks,a.cancel_event),inventoried)
 def finished(report):
  w.last_report=report;w.feedback.set(a.tr('Relatório: ')+f"processed={report['processed']}/{report['total']} failed={report['failed']} unsupported={report['unsupported']} cancelled={report['cancelled']} not_started={report['not_started']}\n{report['destination']}/batch_report.json")
  a.status.set(w.feedback.get())
 def start():
  if a.busy:return
  if not w.inventory:return invalid(a.tr('Faça o inventário antes de extrair.'))
  current=(str(Path(w.source_var.get()).resolve()),w.loose_var.get(),w.banks_var.get())
  if current!=w.inventory_options:return invalid(a.tr('Opções mudaram; refaça o inventário.'))
  destination=w.destination_var.get()
  if not destination:return invalid(a.tr('Selecione instalação e destino.'))
  try:batch_extract.destination_safe(destination,w.inventory['root'])
  except Exception as e:return invalid(e)
  inv=w.inventory;extract_media=w.media_var.get();indices={x['relative']:i for i,x in enumerate(inv['items'],1)}
  archive_status=lambda name,n,total:a.events.put(('progress',indices[name]-1,max(1,len(inv['items'])),f"{indices[name]}/{len(inv['items'])} | {name} | files {n}/{total}"))
  a.worker(lambda:batch_extract.run(inv,destination,a.cancel_event,lambda n,total:a.events.put(('progress',n,max(1,total))),extract_media,archive_status),finished)
 original_scan=scan
 def scan_with_options():
  w.inventory_options=(str(Path(w.source_var.get()).resolve()),w.loose_var.get(),w.banks_var.get());original_scan()
 row=ttk.Frame(b);row.pack(fill='x',pady=8)
 w.inventory_button=ttk.Button(row,text=a.tr('Inventariar sem extrair'),command=scan_with_options);w.inventory_button.pack(side='left')
 w.start_button=ttk.Button(row,text=a.tr('Iniciar extração em lote'),command=start);w.start_button.pack(side='left',padx=8)
 ttk.Button(row,text=a.tr('Cancelar tarefa'),command=a.cancel).pack(side='right')
 w.open_button=ttk.Button(b,text=a.tr('Abrir pasta de saída'),command=lambda:os.startfile(w.destination_var.get()) if w.destination_var.get() and Path(w.destination_var.get()).is_dir() else None);w.open_button.pack(anchor='w')
 return w

def export_dialog(a):
 w,b=window(a,'Exportar modelos (Blender)…');selected=a.selected();w.all_var=tk.BooleanVar(value=False)
 ttk.Label(b,text=a.tr('Modelo selecionado: ')+(selected.name if selected else a.tr('Nenhum asset selecionado.')),wraplength=700).pack(fill='x')
 ttk.Checkbutton(b,text=a.tr('Todos os modelos FM6S da origem aberta'),variable=w.all_var).pack(anchor='w',pady=8)
 w.format_vars={}
 row=ttk.Frame(b);row.pack(fill='x')
 for fmt in ('fbx','blend','glb'):
  v=tk.BooleanVar(value=fmt=='fbx');w.format_vars[fmt]=v;ttk.Checkbutton(row,text='.'+fmt,variable=v).pack(side='left',padx=8)
 w.destination_var=path_row(a,w,b,'Destino novo ou vazio fora do jogo')
 w.manual_var=path_row(a,w,b,'Esqueleto nativo opcional (arquivo 20SE / ES02 ou SSG)',False)
 ttk.Label(b,text=a.tr('Blender opcional: configure o executável oficial em Configurações. Sem Blender, a extração bruta continua disponível.'),wraplength=700).pack(fill='x',pady=8)
 ttk.Label(b,text=a.tr('Limite do rig: hierarquia e rest pose nativas podem ser exportadas SEM vínculo. Paleta/skin ainda não comprovadas; sem pesos, animação ou armature inventada. Materiais: diffuse resolvido em PNG, UV; shaders originais não reproduzidos. GLB pode dividir vértices nas seams.'),wraplength=700).pack(fill='x',pady=8)
 def finish(r):w.last_report=r;w.feedback.set(a.tr('Relatório: ')+f"processed={r['processed']}/{r['total']} failed={r['failed']} cancelled={r['cancelled']}\n{r['destination']}\n"+a.tr('Rig nativo sem vínculo; skin/paleta não comprovadas.'));a.status.set(w.feedback.get())
 def start():
  if a.busy:return
  formats=[fmt for fmt,v in w.format_vars.items() if v.get()];assets=list(a.assets);models=[x for x in assets if x.read_head(4)==b'FM6S'] if w.all_var.get() else ([selected] if selected and selected.read_head(4)==b'FM6S' else [])
  if not models or not formats or not w.destination_var.get():w.feedback.set(a.tr('Selecione modelo, formato e destino.'));return
  dest=Path(w.destination_var.get());manual=w.manual_var.get() or None;executable=a.dep_vars['blender'].get().strip() or blender_export.blender_path()
  try:
   batch_extract.destination_safe(dest,models[0].source or dest.parent)
   if dest.exists() and any(dest.iterdir()):raise ValueError(a.tr('Destino deve ser novo ou vazio.'))
   if not executable or not Path(executable).is_file():raise ValueError(a.tr('Blender não encontrado. Configure em Configurações.'))
  except Exception as e:w.feedback.set(str(e));return
  def work():
   dest.mkdir(parents=True,exist_ok=True);r={'destination':str(dest),'total':len(models),'processed':0,'failed':0,'cancelled':False,'entries':[]};used=set()
   for i,asset in enumerate(models):
    if a.cancel_event.is_set():r['cancelled']=True;break
    name=f'model_{i:05d}';folder=dest/name
    try:
     report=blender_export.export(asset,assets,folder,formats,executable,manual,a.cancel_event);r['processed']+=1;r['entries'].append({'source':asset.name,'status':'processed','folder':name,'report':report})
    except Exception as e:
     if a.cancel_event.is_set():r['cancelled']=True
     else:r['failed']+=1
     r['entries'].append({'source':asset.name,'status':'cancelled' if r['cancelled'] else 'failed','reason':str(e)})
    a.events.put(('progress',r['processed'],len(models)))
    if r['cancelled']:break
   with (dest/'model_export_report.json').open('x',encoding='utf-8') as f:json.dump(r,f,indent=2)
   return r
  a.worker(work,finish)
 row=ttk.Frame(b);row.pack(fill='x',pady=8)
 w.start_button=ttk.Button(row,text=a.tr('Exportar e verificar no Blender'),command=start);w.start_button.pack(side='left')
 ttk.Button(row,text=a.tr('Cancelar tarefa'),command=a.cancel).pack(side='right')
 ttk.Button(b,text=a.tr('Abrir pasta de saída'),command=lambda:os.startfile(w.destination_var.get()) if w.destination_var.get() and Path(w.destination_var.get()).is_dir() else None).pack(anchor='w')
 return w
