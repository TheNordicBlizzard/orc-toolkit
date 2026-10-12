"""Original dark editor shell, retaining the native Tk/WGL viewport."""
from tkinter import ttk
import tkinter as tk

class Tooltip:
 def __init__(self,widget,owner,text):
  self.widget=widget;self.owner=owner;self.text=text;self.timer=None;self.window=None
  widget.bind('<Enter>',self.enter,add='+');widget.bind('<Leave>',self.hide,add='+');widget.bind('<ButtonPress>',self.hide,add='+');widget.bind('<Destroy>',self.hide,add='+')
 def enter(self,event=None):
  self.hide();self.timer=self.widget.after(650,self.show)
 def show(self):
  self.timer=None
  if self.owner.closed or not self.widget.winfo_ismapped():return
  self.window=tk.Toplevel(self.widget);self.window.overrideredirect(True)
  self.window.geometry(f'+{self.widget.winfo_rootx()+8}+{self.widget.winfo_rooty()+self.widget.winfo_height()+5}')
  ttk.Label(self.window,text=self.owner.tr(self.text),padding=8,wraplength=350).pack()
 def hide(self,event=None):
  if self.timer is not None:self.widget.after_cancel(self.timer);self.timer=None
  if self.window is not None:self.window.destroy();self.window=None

def capture_window(app):
 """Actual target Tk client + actual same-process GPU framebuffer.
 PrintWindow omits NVIDIA WGL child contents. Restore only those real pixels,
 without screen scraping other windows, drawing a mockup or CPU rendering.
 """
 import ctypes
 from PIL import ImageGrab
 root=app.root;root.update()
 image=ImageGrab.grab(window=ctypes.windll.user32.GetAncestor(root.winfo_id(),2))
 if app.gpu.ready and app.gpu.winfo_ismapped() and app.canvas.winfo_ismapped() and (app.mesh is not None or app.image is not None):
  frame=app.gpu.snapshot();image.paste(frame,(app.gpu.winfo_rootx()-root.winfo_rootx(),app.gpu.winfo_rooty()-root.winfo_rooty()))
 return image

def apply(root):
 style=ttk.Style(root);style.theme_use('clam')
 bg='#202124';panel='#292b2f';text='#f2f3f5';muted='#adb0b7';accent='#83bcf1'
 root.configure(background=bg)
 root.option_add('*Text.Font','{Segoe UI} -13');root.option_add('*Menu.Font','{Segoe UI} -13')
 root.option_add('*Text.background',bg);root.option_add('*Text.foreground',text)
 root.option_add('*Text.insertBackground',text);root.option_add('*Text.selectBackground','#3c5367')
 root.option_add('*Menu.background',panel);root.option_add('*Menu.foreground',text)
 root.option_add('*Menu.activeBackground','#3c5367');root.option_add('*Menu.activeForeground',text)
 style.configure('.',background=bg,foreground=text,font=('Segoe UI',-13),bordercolor=bg,lightcolor=bg,darkcolor=bg)
 style.configure('TFrame',background=bg)
 style.configure('TLabel',padding=(0,2));style.configure('Muted.TLabel',foreground=muted,font=('Segoe UI',-12))
 style.configure('Title.TLabel',font=('Segoe UI',-22,'bold'));style.configure('Heading.TLabel',font=('Segoe UI',-15,'bold'))
 style.configure('Brand.TLabel',font=('Segoe UI',-18,'bold'),foreground=accent)
 style.configure('Section.TLabel',font=('Segoe UI',-13,'bold'))
 style.configure('TButton',background=panel,padding=(8,6),borderwidth=0)
 style.configure('TCheckbutton',padding=(0,4),indicatorbackground=panel,indicatorforeground=accent)
 style.map('TCheckbutton',background=[('active',bg)],indicatorbackground=[('selected','#4383b7')])
 style.configure('TEntry',fieldbackground=panel,foreground=text,padding=7,borderwidth=0)
 style.map('TEntry',bordercolor=[('focus',accent)])
 style.configure('TCombobox',fieldbackground=panel,background=panel,arrowcolor=muted,padding=7,borderwidth=0)
 style.map('TCombobox',fieldbackground=[('readonly',panel)],foreground=[('readonly',text)],selectbackground=[('readonly',panel)],selectforeground=[('readonly',text)],bordercolor=[('focus',accent)])
 style.configure('Treeview',background=bg,fieldbackground=bg,foreground=text,rowheight=34,borderwidth=0,font=('Segoe UI',-13))
 style.layout('Treeview',[('Treeview.treearea',{'sticky':'nswe'})])
 style.map('Treeview',background=[('selected','#354a5d')],foreground=[('selected',text)])
 style.configure('TNotebook',background=bg,borderwidth=0,tabmargins=(0,0,0,0))
 style.configure('TNotebook.Tab',background=bg,padding=(12,10),foreground=muted,borderwidth=0)
 style.map('TNotebook.Tab',background=[('selected','#30373e'),('active',panel)],foreground=[('selected',accent)])
 style.configure('TPanedwindow',background='#303237',sashwidth=1)
 style.configure('Vertical.TScrollbar',background=panel,troughcolor=bg,borderwidth=0,arrowsize=10)
 style.configure('Horizontal.TProgressbar',background=accent,troughcolor=bg,borderwidth=0,thickness=2)
 return style
