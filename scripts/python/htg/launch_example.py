"""Launches an example file in a new Houdini window."""
import os
import subprocess
import sys

from pathlib import Path


houdini_bin = Path(os.environ.get("HB"))
houdini_exe = houdini_bin / "houdini.exe"

examples_dir = Path(os.environ.get("HTG_BASEDIR")) / "hip" / "examples"
hip_file = examples_dir / sys.argv[1]

subprocess.Popen(f"{houdini_exe} {hip_file}", shell=True)
