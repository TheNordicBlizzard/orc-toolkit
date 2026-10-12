"""Explicit opt-in QA fixtures; no personal paths or game files are shipped."""
import os
from pathlib import Path

def required(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError('Private QA requires environment variable ' + name + '; see BUILD_REDISTRIBUTION.md')
    return Path(value)

def fixture(name):
    return required('ORC_QA_FIXTURE_ROOT') / name

def game():
    return required('ORC_QA_GAME_ROOT')

def scratch():
    return required('ORC_QA_SCRATCH')

def asset(name):
    return required('ORC_QA_ASSET_ROOT') / name
