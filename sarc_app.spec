# sarc_app.spec
# Cross-platform PyInstaller spec for macOS + Windows

import os
import sys
import shutil
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# --------------------------------------------------------------------
# Detect platform and set binary paths
# --------------------------------------------------------------------
binaries = []

if sys.platform == "win32":
    binaries = [
        (shutil.which("dcm2niix"), "."),
        (shutil.which("TotalSegmentator"), "."),
        (shutil.which("pandoc"), "."),
    ]
else:
    binaries = [
        ("/Users/jishaansayyed/Documents/SarcopeniaDetectionTool/test_env/bin/dcm2niix", "."),
        ("/Users/jishaansayyed/Documents/SarcopeniaDetectionTool/test_env/bin/TotalSegmentator", "."),
        ("/opt/homebrew/bin/pandoc", "."),
    ]

# --------------------------------------------------------------------
# Datas (shared between mac + win)
# --------------------------------------------------------------------
datas = [
    ("DiCOM_to_nifti.py", "."),
    ("DiCOM_to_nifti.sh", "."),
    ("rule_based_sarcopenia.py", "."),
    ("ai_api.py", "."),
    ("overlay_utils.py", "."),
    ("CT-Muscle-and-Fat-Segmentation", "CT-Muscle-and-Fat-Segmentation"),
    ("results", "results"),
    ("binary_utils.py", "."),
]

# Huggingface/pypandoc/pandas/pyarrow support
hiddenimports = []
hiddenimports += collect_submodules("pandas")
datas += collect_data_files("pandas")
datas += collect_data_files("pyarrow")
datas += collect_all("pypandoc")[0]
datas += collect_all("huggingface_hub")[0]

block_cipher = None

# --------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------
script_path = os.path.abspath(os.path.join(os.getcwd(), "sarc_app.py"))
a = Analysis(
    [script_path],
    pathex=[os.getcwd()],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SarcopeniaApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    onefile=True,
    windowed=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SarcopeniaApp",
)