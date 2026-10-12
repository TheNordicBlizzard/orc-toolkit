"""Package only explicitly reviewed source/docs files, never a working tree."""
import argparse
from pathlib import Path, PurePosixPath
import zipfile


def package(root, output):
    root = root.resolve()
    entries = [line.strip() for line in (root / 'release-files.txt').read_text(encoding='utf-8').splitlines()
               if line.strip() and not line.lstrip().startswith('#')]
    if len(entries) != len(set(entries)):
        raise ValueError('Duplicate allowlist entries')
    sources = []
    for entry in entries:
        relative = PurePosixPath(entry)
        allowed_suffixes = {'.py', '.md', '.txt', '.spec', '.yml'}
        allowed_images = {'docs/menu.png', 'docs/screenshots/welcome_en.png',
                          'docs/screenshots/welcome_pt-BR.png',
                          'docs/screenshots/settings_en.png',
                          'docs/screenshots/settings_pt-BR.png'}
        reviewed_notice = (entry.startswith('asset_explorer/THIRD_PARTY_LICENSES/')
                           and (relative.suffix.lower() in {'', '.txt', '.md', '.terms', '.h', '.apache', '.bsd'}
                                or relative.name.endswith(('-COPYING', '-LICENSE'))
                                or relative.name == 'font-notices.json'))
        reviewed_inventory = entry in {'asset_explorer/native.spdx.json',
                                       'asset_explorer/compliance_manifest.json'}
        if (relative.suffix.lower() not in allowed_suffixes and entry not in allowed_images
                and entry not in {'LICENSE', '.gitignore', 'addon/orc_native_bridge/LICENSE',
                                  'addon/orc_native_bridge/ALBAM_LICENSE'}
                and not reviewed_notice and not reviewed_inventory):
            raise ValueError('Non-source or unreviewed image entry: ' + entry)
        source = root.joinpath(*relative.parts)
        if relative.is_absolute() or '..' in relative.parts or source.is_symlink() or not source.is_file():
            raise ValueError('Invalid or missing allowlisted source: ' + entry)
        source.resolve().relative_to(root)
        sources.append((source, entry))
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for source, entry in sources:
            archive.write(source, entry)
    with zipfile.ZipFile(output) as archive:
        if archive.namelist() != entries or archive.testzip() is not None:
            raise ValueError('Package readback failed')
    return len(entries)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print('Verified allowlisted entries:', package(args.root, args.output))
