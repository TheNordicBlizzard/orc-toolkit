"""Use the installed Microsoft runtime for wheel-renamed MSVCP imports.

No Microsoft DLL is shipped. The source is restricted to Windows System32;
only the process-private PyInstaller extraction directory receives an alias.
"""
import ctypes
import json
import pathlib
import shutil
import sys

root = pathlib.Path(sys._MEIPASS).resolve()
buffer = ctypes.create_unicode_buffer(32768)
if not ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer)):
    raise RuntimeError('Could not locate the Windows system runtime directory')
system = pathlib.Path(buffer.value)
for alias in json.loads((root / 'external_runtime_aliases.json').read_text()):
    relative = pathlib.PurePosixPath(alias['destination'])
    if relative.is_absolute() or '..' in relative.parts:
        raise RuntimeError('Invalid external runtime alias')
    source = system / alias['system_name']
    if not source.is_file():
        raise RuntimeError('Install Microsoft Visual C++ v14 x64 from https://aka.ms/vc14/vc_redist.x64.exe')
    destination = root.joinpath(*relative.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
