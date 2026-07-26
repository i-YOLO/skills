#!/usr/bin/env python3
"""Delegate shared environment checks to the installed madem skill."""

from __future__ import annotations

import os
import sys
from pathlib import Path


target = Path(__file__).resolve().parents[2] / "madem" / "scripts" / "doctor.py"
if not target.exists():
    raise SystemExit("madem doctor not found. Install madem alongside sync-explainer-video.")
os.execv(sys.executable, [sys.executable, str(target), *sys.argv[1:]])
