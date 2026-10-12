# Redistributable candidate build / Build do candidato redistribuível

## Target / Plataforma
Windows 10/11 **x64**, hardware OpenGL, Microsoft Visual C++ v14 x64 runtime installed. The runtime is an **external prerequisite**, not copied from System32. Official download and terms: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist and https://aka.ms/vc14/vc_redist.x64.exe . No runtime installer is embedded or automatically executed. A current system test is not a clean-machine test or a guarantee for every GPU.

Windows UCRT/API-set DLLs are OS components on Windows 10/11 and are not redistributed: https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment . Windows 7/8/XP and 32-bit Windows are not supported by this package. Graphics drivers/OpenGL32 are supplied by Windows/GPU vendor, not bundled. FFmpeg, vgmstream and Blender remain optional external dependencies.

Windows 10/11 x64: o UCRT pertence ao sistema. O runtime Microsoft Visual C++ v14 x64 deve estar instalado pelo pacote oficial acima. Nenhum instalador é executado automaticamente. Sem suporte a Windows antigo/32-bit; drivers não são redistribuídos.

## Build
Use a Windows x64 Python with Tk, NumPy, Pillow, CustomTkinter, ModernGL, glcontext, pyopengltk, PyOpenGL, PyYAML and PyInstaller installed. Build from this directory:

```
python -m PyInstaller --clean --noconfirm --distpath dist --workpath build ORC_Asset_Explorer.spec
```

`hooks/hook-OpenGL.py` collects only the Windows platform/array plugins and excludes `OpenGL/DLLS` before dependency scanning. `hooks/runtime_external_vc.py` handles NumPy's wheel-renamed MSVCP import: it copies the already installed System32 `msvcp140.dll` to the expected name only inside the process-private PyInstaller extraction directory. No Microsoft DLL bytes are included in the EXE/ZIP and no Windows file is modified. The actual tested system runtime is x64 version 14.51.36247.0; this is an observed version, not a newly established minimum. The app creates its context with WGL through pyopengltk and renders with ModernGL; it never calls GLUT/GLE. The spec excludes their Python wrappers too. UCRT/API sets and VC runtime DLLs are removed from the bundle, with the explicit OS/runtime requirements above. `blender_worker.py` and all opt-in QA runners are included. Complete third-party notices are embedded and must also accompany the release ZIP; do not release an EXE by itself without its notices/SBOM/manifest.

The audit ties native files to extracted CArchive bytes, Analysis sources and official package/archive hashes. `compliance_manifest.json` distinguishes resolved notice/provenance findings from open verification limits; it is not a blanket legal opinion. CPython binary files remain unmodified from the hash-matched official standalone archive. Application packaging differs: unused OpenGL DLLs and externally supplied Microsoft/Windows runtimes are excluded.

## Private QA fixtures (never included in release)
The frozen switches remain opt-in. Set these environment variables to **your own** authorized local fixtures before using them:

- `ORC_QA_FIXTURE_ROOT`: Ada/Tweed original backup fixtures (`adawong.ssg.original.bak`, `tweed.ssg.original.bak`).
- `ORC_QA_GAME_ROOT`: read-only installed-game root used by integration QA.
- `ORC_QA_ASSET_ROOT`: locally extracted authorized audio/video/skeleton fixtures with the runners' documented relative paths.
- `ORC_QA_SCRATCH`: dedicated writable QA scratch directory, never the game installation/source repository.

QA records may contain private paths and copyrighted screenshots; keep all QA results outside public packages. The settings runners restore configuration bytes; isolated portable copies keep these changes out of normal user preferences. Full-export QA inventories the installation but extracts only a reduced fixture subset.

As variáveis apontam apenas para fixtures autorizadas do usuário. Não distribuir jogos, imagens de prévias privadas, logs locais nem configuração pessoal. Testes de extração completa executam somente subconjunto reduzido.
