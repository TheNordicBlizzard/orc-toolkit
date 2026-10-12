"""Create a NEW native positions-only project; explicit file integration only."""
import argparse
from pathlib import Path
import sys

# Use only this checkout's sibling addon, never a developer-home fallback.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'addon'))
from orc_native_bridge.project import create_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--sidecar', type=Path)
    args = parser.parse_args()
    print(create_project(args.template, args.destination, args.sidecar))


if __name__ == '__main__':
    main()
