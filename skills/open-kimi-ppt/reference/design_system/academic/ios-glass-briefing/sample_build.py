"""Reference implementation of the iOS Glass Briefing template — the same 4 module-driven pages as
ink-ivory-briefing/sample_build.py, rendered with theme="ios-glass" (Kit writes media/wall.jpg and
media/wall-cover.jpg and bakes the rounded cover photo).

Run:  python sample_build.py <out_dir>
"""
import runpy
import sys
from pathlib import Path

sample = runpy.run_path(str(Path(__file__).resolve().parents[1] / "ink-ivory-briefing" / "sample_build.py"))
sample["build"](sys.argv[1] if len(sys.argv) > 1 else "sample_out", "ios-glass")
