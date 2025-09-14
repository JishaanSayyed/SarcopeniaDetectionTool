# DiCOM_to_nifti.py
import os
import sys
import subprocess
import shutil
import re
from pathlib import Path
from binary_utils import get_dcm2niix_bin

def _log_default(msg):
    print(msg, end="", flush=True)

def dicom_to_nifti(input_base, output_base, patient_id=None, log_callback=None):
    """
    Convert DICOM -> NIfTI using dcm2niix.
    """
    log = log_callback or _log_default

    input_base = Path(input_base)
    if not input_base.exists():
        log(f"Input folder does not exist: {input_base}\n")
        return None

    # Normalize patient id
    if patient_id:
        pid = re.sub(r"\s+", "_", str(patient_id))
        out_dir = Path(output_base) / pid / "nifti"
    else:
        # If output_base already looks like a nifti folder use it, otherwise create .../nifti
        out_dir = Path(output_base)
        if out_dir.name != "nifti":
            out_dir = out_dir / "nifti"

    out_dir.mkdir(parents=True, exist_ok=True)
    log(f"💾 Output NIfTI folder: {out_dir}\n")

    # Locate dcm2niix
    dcm2niix = get_dcm2niix_bin()
    if not dcm2niix:
        log("dcm2niix binary not found. Please install or bundle it.\n")
        return None

    log(f"▶️ Using dcm2niix: {dcm2niix}\n")

    # Runing conversion on each subfolder that contains files
    processed_any = False
    for folder in sorted([p for p in input_base.rglob("*") if p.is_dir()]):
        try:
            files = [f for f in folder.iterdir() if f.is_file() and not f.name.startswith(".")]
        except PermissionError:
            continue
        if not files:
            continue

        processed_any = True
        log(f"   Processing: {folder}\n")
        cmd = [str(dcm2niix), "-z", "y", "-o", str(out_dir), "-f", "%p_%s", str(folder)]
        log(f"   Running: {' '.join(cmd)}\n")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Stream output to log_callback
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            log(line)
        proc.stdout.close()
        ret = proc.wait()
        if ret != 0:
            log(f"   dcm2niix exit code {ret} for {folder}\n")
        else:
            log(f"   conversion finished for {folder}\n")

    if not processed_any:
        log(f"No DICOM-containing subfolders found under: {input_base}\n")
        return None

    # Post-processing: keeping only L3 nifti (if JSON mentions "L3"), else keeping largest nifti
    json_files = sorted(out_dir.glob("*.json"))
    nii_files = sorted(out_dir.glob("*.nii.gz"))

    if not nii_files:
        log(f"⚠️ No NIfTI files created in {out_dir}\n")
        return None

    # Try find L3 JSON
    l3_json = None
    for j in json_files:
        try:
            txt = j.read_text(errors="ignore")
            if re.search(r"\bL3\b", txt, flags=re.IGNORECASE):
                l3_json = j
                break
        except Exception:
            continue

    if l3_json:
        # corresponding NIfTI has same stem + ".nii.gz"
        candidate_nii = out_dir / (l3_json.stem + ".nii.gz")
        if candidate_nii.exists():
            final_name = f"{pid}_L3.nii.gz" if patient_id else f"{l3_json.stem}_L3.nii.gz"
            final_path = out_dir / final_name

            # Move chosen file to final name
            shutil.move(str(candidate_nii), str(final_path))
            log(f"Found L3 file. Kept: {final_path}\n")
        else:
            log(f"L3 JSON found but corresponding NIfTI missing: {candidate_nii}\n")
            final_path = None

    else:
        # No L3 -> keep largest .nii.gz
        largest = max(nii_files, key=lambda p: p.stat().st_size)
        final_name = f"{pid}_largest.nii.gz" if patient_id else f"{largest.stem}_largest.nii.gz"
        final_path = out_dir / final_name
        shutil.move(str(largest), str(final_path))
        log(f"No L3 found — kept largest NIfTI: {final_path}\n")

    # Cleanup: remove everything except final_path
    if final_path:
        for f in out_dir.glob("*"):
            try:
                if f.resolve() == final_path.resolve():
                    continue
            except Exception:
                # fallback compare by name
                if f.name == final_path.name:
                    continue
            # remove files; remove dirs recursively
            try:
                if f.is_dir():
                    shutil.rmtree(f)
                else:
                    f.unlink()
            except Exception as ex:
                log(f"Could not remove {f}: {ex}\n")

        log(f"Cleanup complete. Final file: {final_path}\n")
    else:
        log("No final NIfTI produced.\n")

    return final_path