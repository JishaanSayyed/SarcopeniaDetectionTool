#!/bin/bash

# Usage: ./dicom_to_nifti.sh <input_folder> <output_base> <patient_id>
input_base="$1"
output_base="$2"
patient_id="$3"
APPDIR="$(dirname "$0")"

if [ -z "$input_base" ] || [ -z "$output_base" ] || [ -z "$patient_id" ]; then
    echo "Usage: $0 <input_folder> <output_base> <patient_id>"
    exit 1
fi

# Clean patient_id (replace spaces with underscores)
patient_id=$(echo "$patient_id" | tr ' ' '_')

out_dir="$output_base/$patient_id/nifti"
mkdir -p "$out_dir"

echo "Input: $input_base"
echo "Output: $out_dir"
echo "Converting for patient: $patient_id"
echo "------------------------------------"

# Convert all DICOM subfolders into the nifti folder
find "$input_base" -type d -print0 | while IFS= read -r -d '' folder; do
    if [ "$(find "$folder" -maxdepth 1 -type f | wc -l)" -gt 0 ]; then
        echo "   Processing: $folder"
        "$APPDIR/dcm2niix" -z y -o "$out_dir" -f "%p_%s" "$folder"
    fi
done

echo "Cleaning up NIfTI files for: $patient_id"

# Step 1: If any JSON contains "L3", keep only that NIfTI
l3_json=$(grep -l "L3" "$out_dir"/*.json 2>/dev/null | head -n 1)
if [ -n "$l3_json" ]; then
    l3_file="${l3_json%.json}.nii.gz"
    final_file="$out_dir/${patient_id}_L3.nii.gz"
    echo "   ✅ Found L3 file, renaming to: $final_file"
    find "$out_dir" -type f ! -name "$(basename "$l3_file")" ! -name "$(basename "$l3_json")" -delete
    mv "$l3_file" "$final_file"
    rm -f "$l3_json"
else
    # Step 2: No L3, so keep only the largest NIfTI
    largest_file=$(ls -S "$out_dir"/*.nii.gz 2>/dev/null | head -n 1)
    if [ -n "$largest_file" ]; then
        final_file="$out_dir/${patient_id}_largest.nii.gz"
        echo "   ⚠️ No L3 found, keeping largest file: $final_file"
        find "$out_dir" -type f ! -name "$(basename "$largest_file")" -delete
        mv "$largest_file" "$final_file"
    else
        echo "   No NIfTI files found for patient: $patient_id"
    fi
fi

echo "Finished patient: $patient_id"
echo "Conversion complete!"