# Optional dependencies / Dependências opcionais

## Windows Explorer EXE

**EN:** No separate Python installation is needed for the portable Explorer EXE. Blender is optional for FBX/blend/GLB export; browsing/raw extraction work without it. Hardware GPU/OpenGL drivers are needed for previews; parsing/extraction do not become GPU tasks. The FullExport executable is a locally tested candidate, locally promoted by matching hash but not published. Download external decoders yourself; no FFmpeg, ffprobe, vgmstream or codec DLL redistribution is proposed here. Configure trusted executables in the program's Dependencies section. Saved paths must be updated if you move them.

**PT-BR:** EXE portable dispensa Python separado. Blender é opcional para FBX/blend/GLB; navegação/extração bruta funcionam sem ele. Prévia exige GPU/driver OpenGL de hardware; parsing/extração não viram tarefas GPU. FullExport é candidato local testado, promovido localmente por hash coincidente, mas não publicado. Baixe decoders externos por conta própria; não propomos redistribuir FFmpeg, ffprobe, vgmstream nem DLL de codec. Configure executáveis confiáveis em Dependências. Caminhos salvos precisam atualização se forem movidos.

| Component / Componente | Purpose / Uso | Source and download / Fonte e download |
|---|---|---|
| FFmpeg + ffprobe | FFmpeg decodes common audio and short video previews; ffprobe is optional external inspection and is not executed by this app. / FFmpeg decodifica áudio comum/prévia vídeo; ffprobe é inspeção externa opcional e não é executado pelo app. | [Repository](https://github.com/FFmpeg/FFmpeg), [official download guidance](https://ffmpeg.org/download.html), [Gyan Windows builds — third-party distributor](https://www.gyan.dev/ffmpeg/builds/) |
| vgmstream-cli | Optional Wwise WEM decoding/playback/WAV. / Decode/playback/WAV Wwise WEM opcional. | [Repository](https://github.com/vgmstream/vgmstream), [official releases](https://github.com/vgmstream/vgmstream/releases) |
| GPU driver | Troubleshooting only; use the device vendor's official driver, not third-party driver updaters. / Somente troubleshooting; use driver oficial do fabricante, não atualizadores terceiros. | [NVIDIA](https://www.nvidia.com/Download/index.aspx), [AMD](https://www.amd.com/en/support), [Intel](https://www.intel.com/content/www/us/en/download-center/home.html) |

**Licenses / Licenças:** FFmpeg licensing depends on build options; the locally examined external build reported GPL v3-or-later. vgmstream includes codec libraries with separate notices. Links are not permission to redistribute their binaries. Audit exact DLLs/build licenses and preserve notices before bundling; links-only is the preferred release design. See [third-party inventory](THIRD_PARTY_NOTICES.md).

## Source and Blender workflows / Código-fonte e Blender

The legacy toolkit menu requires Python 3.10+ and Blender for model/FBX/library workflows; the Blender addon runs inside Blender and is not required by Explorer. / Menu legado exige Python 3.10+ e Blender para modelos/FBX/biblioteca; addon roda dentro do Blender e não é exigido pelo Explorer.

- [Python downloads](https://www.python.org/downloads/)
- [Blender downloads](https://www.blender.org/download/)
- [Git source/version control](https://git-scm.com/downloads) — optional for cloning source; not required to run an extracted release / opcional para clonar fonte; não exige Git para rodar ZIP extraído.

Source Explorer imports NumPy, Pillow, ModernGL, glcontext, pyopengltk, PyOpenGL and CustomTkinter; a rebuilt EXE should include its matching runtime components. Installed versions are not automatically proof of the final EXE's embedded versions. PyInstaller is a build tool only. A final dependency manifest must match the build interpreter and frozen archive inventory.

All links in this document are intended to remain inside the release ZIP alongside README and license notices. / Este arquivo com links deve acompanhar README e avisos de licença no ZIP.

Blender export tested in 5.0.1; source-tested Python 3.14. Use trusted official binaries, preserve their licenses, and keep FBX/blend texture PNG bundles together. / Export testado Blender 5.0.1, fonte Python 3.14; executáveis oficiais confiáveis e bundle PNG preservado. [Build](docs/BUILD.md) · [PT-BR](docs/BUILD.pt-BR.md).
