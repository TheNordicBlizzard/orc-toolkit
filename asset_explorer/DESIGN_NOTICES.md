# ORC Asset Explorer — design / references / notices

## Original desktop implementation

The dark editor shell, Tk/ttk styles, contextual tabs, hover/focus states,
primary button, search field and tooltip code are original Python implementations.
They retain the existing native WGL/ModernGL viewport. No web framework, CSS,
HTML, C# source, logos, icons, game parser or copyrighted game assets were copied
from the design references. No continuously animated decorative effects are used.
The existing parsers and their licensing questions remain unchanged.

## Visual references (not incorporated source)

- REE Content Editor, shadowcookie: https://github.com/kagenocookie/REE-Content-Editor
  - Actual layout references reviewed: `.github/overview_01.jpg` and
    `.github/overview_02.jpg` on the master branch.
  - Inspiration: compact toolbar, left asset browser, dominant central viewport,
    contextual editor tabs, right inspector, status/context information.
  - Upstream LICENSE retrieved over HTTPS: MIT, Copyright (c) 2025 shadowcookie.
    https://raw.githubusercontent.com/kagenocookie/REE-Content-Editor/master/LICENSE
- Uiverse: https://uiverse.io and https://github.com/uiverse-io/galaxy
  - Actual homepage element mosaic reviewed:
    https://uiverse.io/assets/home-page-elements-HQ1obJle.png
  - Inspiration only: outlined controls, accent primary actions, clearly focused
    search fields, selected-state tabs/toggles. No individual community component
    source or assets were reused, so no component author is claimed.
  - Galaxy LICENSE retrieved over HTTPS: MIT, Copyright (c) 2023 Uiverse.io.
    https://raw.githubusercontent.com/uiverse-io/galaxy/main/LICENSE

Upstream MIT permits copying with retained notices, but this change deliberately
uses visual inspiration rather than importing either source tree. It does not
change the licensing of existing adapted ORC parsers or external codec binaries.

## Dependencies: user-configured external programs

- FFmpeg and ffprobe: https://ffmpeg.org/download.html
- FFmpeg source: https://github.com/FFmpeg/FFmpeg
- Windows FFmpeg builds (third-party provider linked by FFmpeg):
  https://www.gyan.dev/ffmpeg/builds/
- vgmstream releases: https://github.com/vgmstream/vgmstream/releases
- vgmstream source: https://github.com/vgmstream/vgmstream

ffprobe is optional for external inspection and is not executed by the app.
FFmpeg and vgmstream are optional for media decoding, not for archive browsing,
extraction, hardware-GPU model/texture preview. The UI opens official information
links in the default browser; it does not download or execute installers. Keep
codec-specific licenses. No external decoder was newly bundled into the EXE.

## Screenshots / evidence

Evidence uses actual Tk controls and the actual same-process hardware GPU
framebuffer, not an HTML mockup. Windows PrintWindow fails to include NVIDIA WGL
child contents; target-client captures restore only the framebuffer pixels at
measured native viewport coordinates. This is documented in the evidence JSON
and verified pixel-for-pixel by an integration test. No unrelated desktop apps
are captured for documentation.

Screenshots are local verification evidence from the user's own assets. Do not
redistribute SSG/DDS/model/audio/video assets or private `evidence_*` directories.
Only the asset-free welcome screenshot is intended as a general documentation
image. No git publishing, release or staging operation was performed.
