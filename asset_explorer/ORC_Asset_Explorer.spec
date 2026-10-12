# Windows 10/11 x64 candidate. No system DLL redistribution.
import json
from pathlib import Path
from PyInstaller.utils.hooks import collect_all
source = Path(SPECPATH)
datas = [(str(source / 'blender_worker.py'), '.')]
binaries = []
hiddenimports = ['OpenGL.platform.win32', 'OpenGL.arrays.numpymodule']
for package in ('customtkinter', 'moderngl', 'glcontext', 'pyopengltk'):
    data, binary, hidden = collect_all(package)
    datas += data
    binaries += binary
    hiddenimports += hidden
license_dir = source / 'THIRD_PARTY_LICENSES'
if license_dir.is_dir():
    datas += [(str(license_dir), 'THIRD_PARTY_LICENSES')]
a = Analysis([str(source / 'app.py')], pathex=[str(source)], binaries=binaries,
             datas=datas, hiddenimports=hiddenimports, hookspath=[str(source / 'hooks')],
             hooksconfig={}, runtime_hooks=[str(source / 'hooks/runtime_external_vc.py')], excludes=['OpenGL.GLUT','OpenGL.GLE'], noarchive=False)
# UCRT/API sets are inbox OS components on Windows 10/11. VC runtime is an
# explicit external prerequisite from Microsoft's official x64 redistributable.
# Never redistribute DLLs harvested from System32 or Windows Performance Toolkit.
def external_runtime(entry):
    name = Path(entry[0]).name.lower()
    return name.startswith(('api-ms-win-', 'ext-ms-win-', 'vcruntime', 'msvcp')) or name == 'ucrtbase.dll'
# NumPy's repaired wheel references a hash-renamed MSVCP DLL. Provide an
# extraction-local alias of the installed official prerequisite, not its wheel copy.
aliases = [{'destination':entry[0].replace('\\', '/'), 'system_name':'msvcp140.dll'}
           for entry in a.binaries if Path(entry[0]).name.lower().startswith('msvcp140-')]
alias_file = Path(workpath) / 'external_runtime_aliases.json'
alias_file.write_text(json.dumps(aliases), encoding='utf-8')
a.datas += [('external_runtime_aliases.json', str(alias_file), 'DATA')]
a.binaries = [entry for entry in a.binaries if not external_runtime(entry)]
a.datas = [entry for entry in a.datas if not external_runtime(entry)]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
          name='ORC_Asset_Explorer_Redistributable_Candidate', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False)
