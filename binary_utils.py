import os
import sys
from pathlib import Path

def _resolve_binary(name_unix: str, name_win: str):
    """
    Resolve binary path depending on platform and whether running frozen (PyInstaller).
    """
    exe_name = name_win if sys.platform == "win32" else name_unix

    # Case 1: Running from PyInstaller bundle
    if getattr(sys, "frozen", False):
        base_dir = Path(sys._MEIPASS)   # PyInstaller unpack dir (_internal)
        candidate = base_dir / exe_name
        if candidate.exists():
            return str(candidate)

    # Case 2: Local venv (developer mode)
    candidate = Path(sys.executable).parent / exe_name
    if candidate.exists():
        return str(candidate)

    # Case 3: Current working directory
    candidate = Path.cwd() / exe_name
    if candidate.exists():
        return str(candidate)

    # Case 4: System PATH
    return exe_name


def get_totalseg_bin():
    return _resolve_binary("TotalSegmentator", "TotalSegmentator.exe")

def get_dcm2niix_bin():
    return _resolve_binary("dcm2niix", "dcm2niix.exe")

def get_pandoc_bin():
    return _resolve_binary("pandoc", "pandoc.exe")