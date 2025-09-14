import os
import sys
import types
if "pyarrow" not in sys.modules:
    fake_pa = types.ModuleType("pyarrow")
    fake_pa.__version__ = "0.0.0"
    sys.modules["pyarrow"] = fake_pa

import pandas as pd

def calculate_sarcopenia(patient_folder: str, output_csv: str):
    """
    Rule-based sarcopenia calculation for a single patient folder.
    Expected structure:
      patient_folder/
        segmentation/
          body_composition_2d.csv
          metadata.csv
    """

    seg_dir = os.path.join(patient_folder, "segmentation")
    bodycomp_path = os.path.join(seg_dir, "body_composition_2d.csv")
    metadata_path = os.path.join(seg_dir, "metadata.csv")

    if not os.path.exists(bodycomp_path) or not os.path.exists(metadata_path):
        print(f"Missing files in {seg_dir}")
        return

    # Load files
    body_df = pd.read_csv(bodycomp_path)
    meta_df = pd.read_csv(metadata_path)

    if body_df.empty or meta_df.empty:
        print(f"Empty files in {seg_dir}, skipping...")
        return

    meta = meta_df.iloc[0]

    # --- Handle missing (NaN) values: prefer user input, else fallback to scanned ---
    patient_name = meta.get("PatientName", "NA")
    sex = meta.get("Gender") if pd.notna(meta.get("Gender")) else meta.get("PatientSex", "NA")
    age = meta.get("Age") if pd.notna(meta.get("Age")) else meta.get("PatientAge", "NA")
    height_cm = meta.get("Height") if pd.notna(meta.get("Height")) else meta.get("TableHeight", None)
    weight_kg = meta.get("Weight") if pd.notna(meta.get("Weight")) else meta.get("ScannedWeight_kg", "NA")

    # --- Body composition ---
    muscle_area = body_df["muscle_area_mm2"].iloc[0]
    vfat_area = body_df.get("vfat_area_mm2", pd.Series([0])).iloc[0]
    sfat_area = body_df.get("sfat_area_mm2", pd.Series([0])).iloc[0]
    mfat_area = body_df.get("mfat_area_mm2", pd.Series([0])).iloc[0]

    if pd.isna(height_cm):
        print(f"Missing height for {patient_name}, skipping...")
        return

    # Convert to m²
    height_m2 = (height_cm / 100.0) ** 2
    smi = muscle_area / height_m2

    # --- Rule-based threshold ---
    if sex == "M":
        sarcopenia = smi < 52.4
    elif sex == "F":
        sarcopenia = smi < 38.5
    else:
        sarcopenia = smi < 45.0

    result = {
        "ID": os.path.basename(patient_folder),
        "PatientName": patient_name,
        "Sex": sex,
        "Age": age,
        "Height_cm": height_cm,
        "Weight_kg": weight_kg,
        "SMI": round(smi, 2),
        "MuscleArea_mm2": muscle_area,
        "VfatArea_mm2": vfat_area,
        "SfatArea_mm2": sfat_area,
        "MfatArea_mm2": mfat_area,
        "Sarcopenia": "Yes" if sarcopenia else "No"
    }

    # Save results
    pd.DataFrame([result]).to_csv(output_csv, index=False)
    print(f"✅ Saved sarcopenia predictions to {output_csv}")


def main():
    """CLI entrypoint"""
    if len(sys.argv) < 3:
        print("❌ Usage: python rule_based_sarcopenia.py <patient_folder> <output_csv>")
        sys.exit(1)

    patient_folder = sys.argv[1]
    output_csv = sys.argv[2]
    calculate_sarcopenia(patient_folder, output_csv)


if __name__ == "__main__":
    main()