# Windows WGL/ModernGL app does not call GLUT or GLE.
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
hiddenimports = ['OpenGL.platform.win32'] + collect_submodules('OpenGL.arrays')
# Do not collect the wheel's unrelated GLUT/GLE DLL directory. Filtering here
# precedes dependency scanning, so obsolete MSVCR100 is never discovered.
datas = collect_data_files('OpenGL', excludes=['DLLS/**'])
